"""
Entity extraction using LangChain + Groq with proper error handling
"""
import os
import json
import re
from typing import Dict, List, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Initialize Groq LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def call_groq_langchain(system_prompt: str, user_message: str) -> str:
    """
    Call Groq API using LangChain for proper integration
    """
    if not GROQ_API_KEY:
        return ""
    
    try:
        llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=1024
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_message)
        ])
        
        chain = prompt | llm
        response = chain.invoke({})
        return response.content
    except Exception as e:
        print(f"Error calling Groq API via LangChain: {e}")
        return ""

def extract_entities_fast(text: str) -> Dict[str, Any]:
    """
    Fast entity extraction using Groq API
    """
    system_prompt = """Extract literary entities from the provided text. Return ONLY valid JSON with these fields:
- characters: list of character names (strings)
- locations: list of location names (strings)
- objects: list of important objects (strings)
- events: list of events that occur (strings)
- summary: 1-2 sentence summary of the text

Example JSON response:
{{"characters": ["John", "Mary"], "locations": ["London"], "objects": ["sword"], "events": ["battle"], "summary": "..."}}"""
    
    user_message = f"Extract entities from this text:\n\n{text[:1000]}\n\nRespond with ONLY the JSON object."
    
    response_text = call_groq_langchain(system_prompt, user_message)
    
    if not response_text:
        return get_fallback_entities(text)
    
    try:
        # Try to parse JSON directly
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                return get_fallback_entities(text)
        except:
            return get_fallback_entities(text)
    
    return {
        "characters": [{"text": c, "type": "character"} for c in result.get("characters", [])],
        "locations": [{"text": l, "type": "location"} for l in result.get("locations", [])],
        "objects": [{"text": o, "type": "object"} for o in result.get("objects", [])],
        "events": [{"text": e, "type": "event"} for e in result.get("events", [])],
        "time_references": [],
        "summary": result.get("summary", text[:100])
    }

def get_fallback_entities(text: str) -> Dict[str, Any]:
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
    system_prompt = "You are a literary expert. Create a concise 1-2 sentence summary of the provided text."
    user_message = text[:500]
    
    response = call_groq_langchain(system_prompt, user_message)
    return response if response else (text[:100] + "..." if len(text) > 100 else text)

def generate_scene_suggestion(context: str) -> str:
    """Generate creative scene suggestions using Groq"""
    system_prompt = "You are a creative writing assistant. Suggest the next scene based on story context in 2-3 sentences."
    user_message = f"Context:\n\n{context[:500]}\n\nWhat should happen next?"
    
    response = call_groq_langchain(system_prompt, user_message)
    return response if response else "Continue the narrative with a new scene."
