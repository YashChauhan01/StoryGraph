# backend/services/text_processor.py

from fastapi import WebSocket
import asyncio
from collections import deque

class TextStreamProcessor:
    def __init__(self):
        self.buffer = deque(maxlen=1000)  # Sliding window
        self.processing_queue = asyncio.Queue()
    
    async def handle_text_stream(self, websocket: WebSocket):
        """Process incoming text in real-time"""
        while True:
            text_chunk = await websocket.receive_text()
            self.buffer.append(text_chunk)
            
            # Process when paragraph complete (double newline)
            if "\n\n" in text_chunk:
                await self.processing_queue.put(self.get_buffer_text())
    
    def get_buffer_text(self):
        """Get text from buffer for processing"""
        return "".join(self.buffer)