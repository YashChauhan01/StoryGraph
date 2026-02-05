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
    
    async def _get_current_location(self, manuscript_id: str):
        """Get current story location"""
        if manuscript_id in self.context_cache:
            return self.context_cache[manuscript_id].get('location', 'Unknown')
        return 'Unknown'
    
    async def _get_active_arc(self, manuscript_id: str):
        """Get active story arc"""
        if manuscript_id in self.context_cache:
            return self.context_cache[manuscript_id].get('arc', 'Main')
        return 'Main'
    
    async def _get_current_era(self, manuscript_id: str):
        """Get current era/time period"""
        if manuscript_id in self.context_cache:
            return self.context_cache[manuscript_id].get('era', 'Present')
        return 'Present'
    
    async def _get_recent_events(self, manuscript_id: str, limit: int = 10):
        """Get recent events from the story"""
        if manuscript_id in self.context_cache:
            return self.context_cache[manuscript_id].get('events', [])[:limit]
        return []
    
    async def update_context(self, manuscript_id: str, entities: dict, event: dict):
        """Update the context cache with new entities and events"""
        if manuscript_id not in self.context_cache:
            self.context_cache[manuscript_id] = {
                "characters": [],
                "location": "Unknown",
                "arc": "Main",
                "era": "Present",
                "events": []
            }
        
        # Update characters
        for char in entities.get("characters", []):
            char_name = char.get("text") if isinstance(char, dict) else str(char)
            if char_name not in self.context_cache[manuscript_id]["characters"]:
                self.context_cache[manuscript_id]["characters"].append(char_name)
        
        # Update locations
        for loc in entities.get("locations", []):
            loc_name = loc.get("text") if isinstance(loc, dict) else str(loc)
            self.context_cache[manuscript_id]["location"] = loc_name
        
        # Add event to recent events
        if event:
            self.context_cache[manuscript_id]["events"].append(event)