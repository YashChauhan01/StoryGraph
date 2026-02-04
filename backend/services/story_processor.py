# backend/services/story_processor.py

import os
from dotenv import load_dotenv
from services.entity_extractor import EntityExtractor
from services.graph_manager import KnowledgeGraphManager
from services.context_manager import ContextManager

load_dotenv()

class StoryProcessor:
    def __init__(self):
        # Initialize components
        self.entity_extractor = EntityExtractor()
        
        # Neo4j configuration from environment
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
        self.graph_manager = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
        
        # Initialize context manager
        self.context_manager = ContextManager()
        
        # Vector store (placeholder for now)
        self.vector_store = None
    
    async def process_paragraph(self, text: str, metadata: dict):
        """Main processing pipeline"""
        
        # Step 1: Get context
        context = await self.context_manager.get_active_context(
            metadata['manuscript_id']
        )
        
        # Step 2: Extract entities
        entities = await self.entity_extractor.extract_entities(text, context)
        
        # Step 3: Create Event node
        event_data = {
            "text": text,
            "chapter": metadata['chapter'],
            "paragraph": metadata['paragraph'],
            "summary": await self._generate_summary(text)
        }
        
        event = await self.graph_manager.create_event(event_data, context)
        
        # Step 4: Process each entity type
        await self._process_characters(entities['characters'], event['event_id'])
        await self._process_locations(entities['locations'], event['event_id'])
        await self._process_objects(entities['objects'], event['event_id'])
        await self._process_relationships(entities['relationships'], event['event_id'])
        
        # Step 5: Store in vector database for semantic search
        await self.vector_store.add_event(event, text)
        
        # Step 6: Update context
        await self.context_manager.update_context(
            metadata['manuscript_id'],
            entities,
            event
        )
        
        return {
            "event_id": event['event_id'],
            "entities_extracted": entities,
            "status": "processed"
        }
    
    async def _process_characters(self, characters: list, event_id: str):
        """Process extracted characters"""
        
        for char in characters:
            # Create/update character node
            character = await self.graph_manager.create_character({
                "name": char['text'],
                "event_id": event_id
            })
            
            # Link to event
            await self.graph_manager.link_character_to_event(
                character['character_id'],
                event_id,
                action="appears"
            )
    
    async def _generate_summary(self, text: str):
        """Generate event summary using LLM"""
        # Use Qwen or similar to create concise summary
        pass