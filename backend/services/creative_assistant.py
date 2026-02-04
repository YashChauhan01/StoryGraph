# backend/services/creative_assistant.py

import os
from dotenv import load_dotenv
from services.graph_manager import KnowledgeGraphManager

load_dotenv()

class CreativeAssistant:
    def __init__(self):
        # Neo4j configuration from environment
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
        self.graph_manager = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
        
        # LLM placeholder (will be implemented)
        self.llm = None
    
    async def suggest_next_scene(self, manuscript_id: str, context: dict):
        """Generate scene suggestions based on current state"""
        
        # Get active arcs
        active_arcs = await self._get_active_arcs(manuscript_id)
        
        # Analyze arc progression
        arc_analysis = await self._analyze_arc_progression(active_arcs)
        
        # Generate suggestions
        suggestions = await self._generate_scene_suggestions(
            arc_analysis,
            context
        )
        
        return suggestions
    
    async def generate_dialogue(self, character_id: str, situation: str):
        """Generate in-character dialogue"""
        
        # Get character voice profile
        voice_profile = await self._build_voice_profile(character_id)
        
        # Generate dialogue
        prompt = f"""Generate dialogue for this character in this situation:

Character Profile:
{voice_profile}

Situation: {situation}

Write 2-3 lines of dialogue that match this character's established voice.
"""
        
        dialogue = await self.llm.generate(prompt)
        
        return dialogue
    
    async def _build_voice_profile(self, character_id: str):
        """Extract character's speaking patterns"""
        
        with self.graph_manager.driver.session() as session:
            query = """
            MATCH (c:Character {character_id: $character_id})-[:APPEARS_IN]->(e:Event)
            WHERE e.text CONTAINS c.name + ' said' OR e.text CONTAINS c.name + ':'
            
            RETURN e.text AS dialogue
            ORDER BY e.timestamp DESC
            LIMIT 20
            """
            
            results = session.run(query, character_id=character_id)
            dialogues = [record['dialogue'] for record in results]
            
            # Analyze patterns
            analysis_prompt = f"""Analyze these dialogue samples and describe the character's voice:

{chr(10).join(dialogues)}

Describe:
1. Vocabulary level
2. Sentence structure patterns
3. Common phrases
4. Emotional tone
5. Speech quirks
"""
            
            voice_profile = await self.llm.generate(analysis_prompt)
            
            return voice_profile