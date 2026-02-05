import os
from neo4j import GraphDatabase
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

class GraphRAGService:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
        self.llm = ChatGroq(
            temperature=0.3,
            model_name="llama-3.1-8b-instant",
            groq_api_key=os.getenv("GROQ_API_KEY")
        )

    def close(self):
        self.driver.close()

    def _get_narrative_context(self, manuscript_id: str):
        """
        Retrieves the story timeline by following the Manuscript -> Scene link.
        """
        # --- FIXED QUERY ---
        query = """
        MATCH (m:Manuscript {id: $mid})-[:CONTAINS]->(s:Scene)
        
        // Gather Events linked to this scene
        OPTIONAL MATCH (s)-[:INCLUDES_EVENT]->(e:Event)
        
        // Gather Characters appearing in this scene
        OPTIONAL MATCH (c:Character)-[:APPEARS_IN]->(s)
        
        WITH s, e, c
        ORDER BY s.sequence_index ASC
        
        RETURN 
            s.sequence_index as step,
            s.description as scene_desc,
            collect(DISTINCT e.description) as specific_events,
            collect(DISTINCT c.name + ' (Feeling: ' + c.emotion + ', Goal: ' + c.goal + ')') as character_states
        """
        
        with self.driver.session() as session:
            result = session.run(query, mid=manuscript_id)
            records = [record.data() for record in result]
            
            if not records:
                return None

            context_text = f"STORY TIMELINE FOR MANUSCRIPT '{manuscript_id}':\n\n"
            for r in records:
                # Default to Step 0 if index is None
                step = r['step'] if r['step'] is not None else "?"
                context_text += f"SCENE {step}:\n"
                context_text += f"  Summary: {r['scene_desc']}\n"
                
                if r['specific_events']:
                    # Filter out duplicates or empty strings
                    valid_events = [ev for ev in r['specific_events'] if ev]
                    if valid_events:
                        context_text += f"  Details: {', '.join(valid_events)}\n"
                
                if r['character_states']:
                    context_text += f"  Characters: {'; '.join(r['character_states'])}\n"
                context_text += "\n"
                
            return context_text

    async def answer_question(self, manuscript_id: str, question: str):
        context = self._get_narrative_context(manuscript_id)
        
        if not context:
            return "I don't have enough data on this story yet. Please process the text first."

        prompt = ChatPromptTemplate.from_template("""
            You are a Story Expert. You have access to a precise Knowledge Graph of the narrative events.
            
            Based ONLY on the context below, answer the user's question.
            
            STORY CONTEXT (Graph Timeline):
            {context}
            
            USER QUESTION: 
            {question}
            
            GUIDELINES:
            1. **Cite Evidence:** Use "Scene X" references. (e.g., "In Scene 3, she felt joyful because...")
            2. **Trace Changes:** If asking about character growth, compare earlier scenes to later ones.
            3. **Be Specific:** Do not generalize. Use the exact events listed in the context.
        """)
        
        chain = prompt | self.llm
        response = await chain.ainvoke({"context": context, "question": question})
        
        return response.content

rag_service = GraphRAGService()