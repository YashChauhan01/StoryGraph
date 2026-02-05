import asyncio
import re
from typing import Dict, Any, List
from fastapi import WebSocket

class TextStreamProcessor:
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        
        # --- TUNING FOR SHORT STORIES ---
        # Lowered to 200 to ensure "Little Match Girl" gets split into 5-6 scenes
        self.MIN_CHUNK_SIZE = 200 
        self.MAX_CHUNK_SIZE = 4000

    def _chunk_text(self, text: str) -> List[str]:
        """
        Aggressive slicer to guarantee multiple scene generation.
        """
        text = text.strip()
        if not text: return []

        # 1. Normalize Newlines (Handle Windows \r\n and mixed types)
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 2. Try splitting by Double Newlines (Paragraphs)
        raw_chunks = [p.strip() for p in text.split('\n\n') if p.strip()]

        # 3. Fallback: If that didn't work (e.g. text is one block), split by Single Newlines
        if len(raw_chunks) <= 1:
            raw_chunks = [p.strip() for p in text.split('\n') if p.strip()]

        # 4. Emergency Fallback: If still 1 chunk, split by Sentences (Periods)
        if len(raw_chunks) <= 1:
            # Split by period followed by space, keeping the period
            raw_chunks = re.split(r'(?<=[.!?])\s+', text)

        final_chunks = []
        current_chunk = ""

        # 5. Merge logic (Assemble into MIN_CHUNK_SIZE)
        for piece in raw_chunks:
            # If adding this piece keeps us under the limit, merge it
            if len(current_chunk) + len(piece) < self.MIN_CHUNK_SIZE:
                current_chunk += "\n\n" + piece
            else:
                # Chunk is big enough, save it
                if current_chunk:
                    final_chunks.append(current_chunk.strip())
                current_chunk = piece
        
        # Add the last leftover piece
        if current_chunk:
            final_chunks.append(current_chunk.strip())

        return final_chunks

    async def add_to_stream(self, websocket: WebSocket, text: str, metadata: Dict[str, Any]):
        if not text or not text.strip():
            return

        print(f"📚 Analyzing Input: {len(text)} chars...")

        # 1. RUN AGGRESSIVE CHUNKING
        chunks = self._chunk_text(text)
        print(f"✂️ Split into {len(chunks)} Scenes.") # <--- Watch this log!

        base_para = metadata.get('paragraph', 0)
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            # Unique ID for the timeline: 0_0, 0_1, 0_2...
            chunk_metadata['paragraph'] = f"{base_para}_{i}" 
            chunk_metadata['total_chunks'] = len(chunks)
            chunk_metadata['chunk_index'] = i
            chunk_metadata['raw_text'] = chunk  # Store raw text for sentiment analysis
            
            print(f"📥 Queuing Scene {i+1}/{len(chunks)} ({len(chunk)} chars)")
            
            await self.processing_queue.put({
                "websocket": websocket,
                "text": chunk,
                "metadata": chunk_metadata
            })

processor = TextStreamProcessor()