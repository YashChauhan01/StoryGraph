import sys
import asyncio
import uvicorn
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

# Ensure the backend directory is in the python path
sys.path.insert(0, str(Path(__file__).parent))

# --- SERVICE IMPORTS ---
from services.text_processor import processor as text_streamer
from services.story_processor import processor as story_logic

# --- ROUTER IMPORTS ---
# We alias 'character_arc' as 'analytics' to keep the URL path clean
from routers import character_arc as analytics 
from routers import rag

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# --- APP SETUP ---
app = FastAPI(title="StoryGraph API")

# CORS Middleware (Allows your React Frontend to talk to this Backend)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# --- REGISTER ROUTERS ---
app.include_router(analytics.router) # Endpoints: /analytics/character-arc/...
app.include_router(rag.router)       # Endpoints: /rag/query

# --- BACKGROUND WORKER ---
async def extraction_worker():
    """
    Consumes chunks from the queue and processes them through the Story Processor.
    This runs in the background so the WebSocket stays responsive.
    """
    print("⚙️ Worker: Online and listening to queue...")
    while True:
        # Get a job from the queue
        job = await text_streamer.processing_queue.get()
        websocket, text, metadata = job['websocket'], job['text'], job['metadata']
        
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                # 1. Extract Entities (AI + Graph Logic)
                result = await story_logic.process_paragraph(text, metadata)
                
                # 2. Send 'Success' signal back to Frontend
                # Note: We send the full result mostly for debugging/visualization on the front end
                await websocket.send_json({
                    "type": "entities_extracted", 
                    "data": result,
                    "paragraph_index": metadata.get('chunk_index')
                })
                
                print(f"🚀 Sent results for Paragraph {metadata.get('paragraph')}")
                
        except Exception as e:
            print(f"❌ Worker Error: {e}")
        finally:
            # Mark job as done so the queue knows
            text_streamer.processing_queue.task_done()

# --- STARTUP EVENT ---
@app.on_event("startup")
async def startup_event():
    # Start the background worker when the API starts
    asyncio.create_task(extraction_worker())

# --- WEBSOCKET ENDPOINT ---
@app.websocket("/ws/manuscript/{manuscript_id}")
async def websocket_endpoint(websocket: WebSocket, manuscript_id: str):
    """
    Handles real-time text streaming from the frontend.
    """
    await websocket.accept()
    print(f"✓ Connected: {manuscript_id}")
    
    try:
        while True:
            # Receive JSON from Frontend
            data = await websocket.receive_json()
            
            # Send text to the Stream Processor (which handles chunking & queuing)
            # We default paragraph to 0 if not provided, but the chunker handles sub-indexing (0_1, 0_2...)
            await text_streamer.add_to_stream(
                websocket, 
                data.get('text', ''), 
                {
                    "manuscript_id": manuscript_id, 
                    "chapter": data.get('chapter', 1), 
                    "paragraph": data.get('paragraph', 0)
                }
            )
            
    except WebSocketDisconnect:
        print(f"Disconnected: {manuscript_id}")
    except Exception as e:
        print(f"⚠️ WebSocket loop error: {e}")
    finally:
        # Clean close
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()

# --- ENTRY POINT ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)