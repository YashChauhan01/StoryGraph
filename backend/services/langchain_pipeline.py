"""
Fast entity extraction and text processing using LangChain + Groq
"""
import os
import json
import re
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Initialize Groq LLM
groq_api_key = os.getenv("GROQ_API_KEY")

try:
    llm = ChatGroq(
        api_key=groq_api_key,
        model="llama-3.1-8b-instant",
        temperature=0.3,
        max_tokens=1024
    )
except Exception as e:
    print(f"Warning: Could not initialize Groq LLM: {e}")
    llm = None

def extract_entities_fast(text: str) -> dict:
    """
    Fast entity extraction using Groq LLM
    """
    if not llm:
        return get_fallback_entities(text)
    
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract literary entities from text. Return JSON with these fields:
- characters: list of character names
- locations: list of location names  
- objects: list of important objects
- events: list of events
- summary: 1-2 sentence summary"""),
            ("user", f"Extract entities from:\n\n{text[:1000]}\n\nReturn ONLY valid JSON.")
        ])
        
        chain = prompt | llm
        response = chain.invoke({})
        
        # Parse JSON response
        try:
            result = json.loads(response.content)
        except:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                return get_fallback_entities(text)
        
        return {
            "characters": [{"text": c, "type": "character"} for c in result.get("characters", [])],
            "locations": [{"text": l, "type": "location"} for l in result.get("locations", [])],
            "objects": [{"text": o, "type": "object"} for o in result.get("objects", [])],
            "events": [{"text": e, "type": "event"} for e in result.get("events", [])],
            "time_references": [],
            "summary": result.get("summary", text[:100])
        }
    except Exception as e:
        print(f"Error in Groq entity extraction: {e}")
        return get_fallback_entities(text)

def get_fallback_entities(text: str) -> dict:
    """Fallback simple entity extraction"""
    return {
        "characters": [],
        "locations": [],
        "objects": [],
        "events": [],
        "time_references": [],
        "summary": text[:150] + "..." if len(text) > 150 else text
    }

def generate_summary(text: str) -> str:
    """Generate a concise summary using Groq"""
    if not llm:
        return text[:100] + "..." if len(text) > 100 else text
    
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Create a concise 1-2 sentence summary of the text."),
            ("user", text[:500])
        ])
        
        chain = prompt | llm
        return chain.invoke({}).content
    except Exception as e:
        print(f"Error generating summary: {e}")
        return text[:100] + "..." if len(text) > 100 else text

def generate_scene_suggestion(context: str) -> str:
    """Generate creative scene suggestions using Groq"""
    if not llm:
        return "Continue the narrative with a new scene."
    
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a creative writing assistant. Suggest the next scene in 2-3 sentences."),
            ("user", f"Context:\n\n{context[:500]}\n\nWhat should happen next?")
        ])
        
        chain = prompt | llm
        return chain.invoke({}).content
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return "Continue the narrative with a new scene."
