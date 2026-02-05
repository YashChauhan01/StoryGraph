import os
from langchain_groq import ChatGroq
from services.graph_manager import KnowledgeGraphManager

class CreativeAssistant:
    def __init__(self):
        # 1. Reasoning engine for creative writing
        self.llm = ChatGroq(
            temperature=0.7,  # Higher temperature for more creative/varied prose
            model_name="llama-3.1-70b-versatile",
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        # 2. Access to the graph history
        self.graph_manager = KnowledgeGraphManager(
            os.getenv('NEO4J_URI'),
            os.getenv('NEO4J_USER'),
            os.getenv('NEO4J_PASSWORD')
        )
    
    async def suggest_next_scene(self, manuscript_id: str, context: dict):
        """Generates scene suggestions based on current graph state."""
        # Get active arcs from Neo4j (Level 2 nodes)
        active_arcs = await self._get_active_arcs(manuscript_id)
        
        prompt = f"""
        You are a master novelist. Based on the current story state, suggest the next scene.
        
        CURRENT CONTEXT:
        Location: {context.get('current_location')}
        Characters Present: {context.get('active_characters')}
        Active Plot Arcs: {active_arcs}
        
        Suggest a scene that advances one of these arcs. 
        Focus on sensory details and character tension.
        """
        
        response = await self.llm.ainvoke(prompt)
        return response.content

    async def generate_dialogue(self, character_name: str, situation: str):
        """Generates dialogue using the character's established 'Voice Profile'."""
        
        # Pull past dialogue from Neo4j to match tone
        voice_history = await self._get_character_voice(character_name)
        
        prompt = f"""
        Generate dialogue for {character_name}.
        
        ESTABLISHED VOICE SAMPLES:
        {voice_history}
        
        SITUATION: {situation}
        
        Write 3-4 lines of dialogue. Maintain the character's vocabulary and rhythm.
        """
        
        response = await self.llm.ainvoke(prompt)
        return response.content
    
    async def _get_character_voice(self, character_name: str):
        """Retrieves past dialogue snippets from the Knowledge Graph."""
        async with self.graph_manager.driver.session() as session:
            query = """
            MATCH (c:Character {name: $name})-[:APPEARS_IN]->(e:Event)
            WHERE e.text CONTAINS '"' // Look for quotes in stored event text
            RETURN e.text as line
            ORDER BY e.timestamp DESC
            LIMIT 5
            """
            result = await session.run(query, name=character_name)
            records = await result.data()
            
            if not records:
                return "No established voice yet. Use a standard neutral tone."
            
            return "\n".join([r['line'] for r in records])

    async def _get_active_arcs(self, manuscript_id: str):
        """Queries Neo4j for currently open Level 2 Arc nodes."""
        async with self.graph_manager.driver.session() as session:
            query = """
            MATCH (a:Arc {status: 'active'})
            RETURN a.name as name, a.description as desc
            LIMIT 3
            """
            result = await session.run(query)
            records = await result.data()
            return records if records else "Main Plot"