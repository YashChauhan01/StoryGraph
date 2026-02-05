import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_neo4j import Neo4jVector
from langchain_huggingface import HuggingFaceEmbeddings
from services.graph_manager import KnowledgeGraphManager

load_dotenv()

class QueryEngine:
    def __init__(self):
        # 1. Setup reasoning engine (Groq)
        self.llm = ChatGroq(
            model_name="llama-3.1-70b-versatile", # 70B is better for complex reasoning
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        # 2. Setup semantic memory (Neo4j Vector Store)
        # Using local HuggingFace embeddings to save on API costs
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        self.vector_store = Neo4jVector.from_existing_graph(
            embedding=self.embeddings,
            url=os.getenv('NEO4J_URI'),
            username=os.getenv('NEO4J_USER'),
            password=os.getenv('NEO4J_PASSWORD'),
            index_name="story_entities",
            node_label="Event", # We search across events
            text_node_properties=["text", "summary"],
            embedding_node_property="embedding"
        )
        
        self.graph_manager = KnowledgeGraphManager(
            os.getenv('NEO4J_URI'), 
            os.getenv('NEO4J_USER'), 
            os.getenv('NEO4J_PASSWORD')
        )
    
    async def answer_query(self, question: str, manuscript_id: str):
        """Processes natural language questions about the story."""
        try:
            # Step 1: Extract intent (e.g., character_location)
            intent = await self._classify_query(question)
            
            # Step 2: Semantic search for context
            # asimilarity_search is non-blocking
            relevant_docs = await self.vector_store.asimilarity_search(
                question, 
                k=5, 
                filter={"manuscript_id": manuscript_id}
            )
            
            # Step 3: Graph search for structured data
            graph_context = await self._execute_graph_query(intent, question)
            
            # Step 4: Synthesize the final answer
            return await self._synthesize_answer(question, relevant_docs, graph_context)
            
        except Exception as e:
            print(f"❌ Query Engine Error: {e}")
            return {"answer": "I'm sorry, I couldn't retrieve that information right now.", "sources": []}

    async def _classify_query(self, question: str):
        """Determines if the user is asking about a person, place, or event."""
        prompt = f"Classify the intent of this story question: '{question}'\nTypes: character_info, location_info, plot_timeline. Return ONLY the type name."
        response = await self.llm.ainvoke(prompt)
        return response.content.strip().lower()

    async def _execute_graph_query(self, intent: str, question: str):
        """Uses Cypher to find specific relationships in the graph."""
        # For simplicity, we use a broad 'nearby nodes' query
        # This finds entities connected to the current topic
        async with self.graph_manager.driver.session() as session:
            query = """
            MATCH (e:Event)-[r]-(n)
            WHERE e.text CONTAINS $topic OR n.name CONTAINS $topic
            RETURN n.name as entity, type(r) as relationship, e.text as context
            LIMIT 5
            """
            # Extract a keyword from the question for the graph search
            topic = question.split()[-1] 
            result = await session.run(query, topic=topic)
            records = await result.data()
            return records

    async def _synthesize_answer(self, question, docs, graph_context):
        """Combines all data into a narrative response."""
        context_text = "\n".join([d.page_content for d in docs])
        graph_text = str(graph_context)
        
        prompt = f"""
        Answer the question based ONLY on the story context provided.
        Question: {question}
        
        Textual Context: {context_text}
        Structural Context: {graph_text}
        
        Answer concisely in 2-3 sentences.
        """
        response = await self.llm.ainvoke(prompt)
        return {
            "answer": response.content,
            "sources": [d.metadata for d in docs]
        }