# backend/services/query_engine.py

import os
from dotenv import load_dotenv
from services.graph_manager import KnowledgeGraphManager

load_dotenv()

class QueryEngine:
    def __init__(self):
        # Neo4j configuration from environment
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
        self.graph_manager = KnowledgeGraphManager(neo4j_uri, neo4j_user, neo4j_password)
        
        # Vector store placeholder (will be implemented)
        self.vector_store = None
        
        # LLM placeholder (will be implemented)
        self.llm = None
    
    async def answer_query(self, question: str, manuscript_id: str):
        """Natural language query processing"""
        
        # Step 1: Extract query intent
        intent = await self._classify_query(question)
        
        # Step 2: Search vector store for relevant events
        relevant_events = await self.vector_store.semantic_search(
            question,
            manuscript_id,
            top_k=10
        )
        
        # Step 3: Query graph for specific relationships
        graph_results = await self._execute_graph_query(intent, relevant_events)
        
        # Step 4: Synthesize answer
        answer = await self._synthesize_answer(
            question,
            relevant_events,
            graph_results
        )
        
        return answer
    
    async def _classify_query(self, question: str):
        """Determine query type"""
        
        prompt = f"""Classify this query into one of these types:
        - character_knowledge: "What does X know about Y?"
        - character_location: "Where is X?"
        - event_sequence: "What happened after X?"
        - relationship: "What is X's relationship with Y?"
        - object_status: "Who has the X?"
        
        Query: {question}
        
        Return only the type.
        """
        
        return await self.llm.generate(prompt)
    
    async def _execute_graph_query(self, intent: str, events: list):
        """Execute Cypher query based on intent"""
        
        if intent == "character_knowledge":
            return await self._query_character_knowledge(events)
        elif intent == "character_location":
            return await self._query_character_location(events)
        # ... other intent handlers
    
    async def _query_character_knowledge(self, events: list):
        """What does character know?"""
        
        with self.graph_manager.driver.session() as session:
            query = """
            MATCH (c:Character {name: $character_name})-[:APPEARS_IN]->(e:Event)
            WHERE e.event_id IN $event_ids
            OPTIONAL MATCH (e)-[:INVOLVES]->(other_event:Event)
            
            RETURN c, e, other_event
            ORDER BY e.timestamp
            """
            
            # Execute and return results
            pass
    
    async def _synthesize_answer(self, question, events, graph_results):
        """Use LLM to create natural language answer"""
        
        context = self._format_context(events, graph_results)
        
        prompt = f"""Based on the story context below, answer this question:

Question: {question}

Context:
{context}

Provide a clear answer with chapter references where relevant.
"""
        
        answer = await self.llm.generate(prompt)
        
        return {
            "answer": answer,
            "sources": self._extract_sources(events),
            "related_events": [e['event_id'] for e in events]
        }