import asyncio
import time
from .entity_extractor import EntityExtractor
from .graph_manager import graph_db

class StoryProcessor:
    def __init__(self):
        self.extractor = EntityExtractor()
        self.active_contexts = {}

    async def process_paragraph(self, text: str, metadata: dict):
        manuscript_id = metadata.get("manuscript_id", "default")
        
        # RETRY LOGIC for Rate Limits
        max_retries = 3
        attempt = 0
        
        while attempt < max_retries:
            try:
                # 1. Get Context
                context = self.active_contexts.get(manuscript_id, [])
                
                # 2. Extract (AI)
                entities = await self.extractor.extract(text, metadata, context)
                
                # 3. Save to Neo4j (Bulk Optimized)
                # We run this in a thread to keep the async loop moving
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, graph_db.save_extracted_entities, entities, metadata)
                
                # 4. Update Memory
                new_chars = [c['text'] for c in entities.get('characters', [])]
                self.active_contexts[manuscript_id] = list(set(context + new_chars))[-15:] # Increased memory
                
                return {
                    "event_id": f"evt_{metadata.get('paragraph')}",
                    "entities_extracted": entities,
                    "status": "processed"
                }

            except Exception as e:
                error_str = str(e)
                # Detect Rate Limits (429) or Overloaded Model (503)
                if "429" in error_str or "rate_limit" in error_str.lower():
                    attempt += 1
                    wait_time = 20 * attempt # Linear backoff: 20s, 40s, 60s
                    print(f"⏳ Rate Limit Hit. Cooling down for {wait_time}s... (Attempt {attempt}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Unrecoverable Error: {e}")
                    return {"entities_extracted": {}, "error": error_str}
        
        return {"error": "Max retries exceeded"}

processor = StoryProcessor()