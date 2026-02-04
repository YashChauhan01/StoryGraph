# backend/services/context_manager.py

class ContextManager:
    def __init__(self):
        """Initialize context manager without Redis"""
        self.context_cache = {}
    
    async def get_active_context(self, manuscript_id: str):
        """Retrieve current writing context"""
        
        context = {
            "active_characters": await self._get_recent_characters(manuscript_id),
            "current_location": await self._get_current_location(manuscript_id),
            "current_arc": await self._get_active_arc(manuscript_id),
            "current_era": await self._get_current_era(manuscript_id),
            "recent_events": await self._get_recent_events(manuscript_id, limit=10)
        }
        
        return context
    
    async def _get_recent_characters(self, manuscript_id: str):
        """Get characters mentioned in last 5 paragraphs"""
        # Use in-memory cache instead of Redis
        if manuscript_id in self.context_cache:
            return self.context_cache[manuscript_id].get('characters', [])
        return []