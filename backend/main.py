# backend/main.py

import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Also add CORS headers to WebSocket
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

processor = None

try:
    from services.story_processor import StoryProcessor
    processor = StoryProcessor()
    print("✓ StoryProcessor loaded successfully")
except Exception as e:
    print(f"⚠ Warning: Could not initialize StoryProcessor: {e}")
    print("Using mock processor for development")
    
    # Mock processor for development
    class MockStoryProcessor:
        async def process_paragraph(self, text: str, metadata: dict):
            # Return mock entities for testing
            return {
                "event_id": f"event_{metadata['paragraph']}",
                "entities_extracted": {
                    "characters": [{"text": "Character", "type": "character"}],
                    "locations": [{"text": "Location", "type": "location"}],
                    "objects": [{"text": "Object", "type": "object"}],
                    "events": [{"text": "Event", "type": "event"}]
                },
                "status": "processed"
            }
    
    processor = MockStoryProcessor()

@app.websocket("/ws/manuscript/{manuscript_id}")
async def websocket_endpoint(websocket: WebSocket, manuscript_id: str):
    try:
        await websocket.accept()
        print(f"WebSocket connected for manuscript: {manuscript_id}")
        
        while True:
            # Receive text from editor
            data = await websocket.receive_json()
            print(f"Received data: {data}")
            
            # Process paragraph
            result = await processor.process_paragraph(
                text=data['text'],
                metadata={
                    "manuscript_id": manuscript_id,
                    "chapter": data['chapter'],
                    "paragraph": data['paragraph']
                }
            )
            
            # Send back extracted entities
            await websocket.send_json({
                "type": "entities_extracted",
                "data": result
            })
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1000)
        except:
            pass
    finally:
        await websocket.close()