import os
import json
import re
from typing import List, TypedDict, Annotated, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

class GraphState(TypedDict):
    text: str
    metadata: Dict[str, Any]
    entities: Annotated[Dict[str, Any], lambda old, new: new]
    active_characters: List[str]

class EntityExtractor:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0.1, 
            model_name="llama-3.1-8b-instant", 
            groq_api_key=os.getenv("GROQ_API_KEY"),
            max_tokens=4000 
        )
        self.workflow = self._build_workflow()

    def _sanitize_json_output(self, text: str) -> str:
        """
        Attempts to fix common JSON errors made by LLMs.
        """
        # 1. Strip Markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```', '', text)
        
        # 2. Fix single quotes used as JSON delimiters (risky but necessary for some models)
        # This regex looks for 'key': 'value' patterns and tries to double-quote them
        # It's better to rely on the prompt, but this helps in edge cases.
        
        return text.strip()

    def _surgical_json_parser(self, text: str):
        text = self._sanitize_json_output(text)
        
        # Find start and end of JSON object
        start_idx = text.find('{')
        if start_idx == -1: return None
        
        balance = 0
        in_string = False
        escape = False
        
        for i in range(start_idx, len(text)):
            char = text[i]
            if char == '"' and not escape: in_string = not in_string
            if char == '\\' and not escape: escape = True
            else: escape = False
            
            if not in_string:
                if char == '{': balance += 1
                elif char == '}': 
                    balance -= 1
                    if balance == 0:
                        json_str = text[start_idx : i + 1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            # If standard parsing fails, try "dirty" fixes
                            # Fix 1: Add quotes to unquoted keys
                            fixed_str = re.sub(r'(?<!")(\b\w+\b)(?=\s*:)', r'"\1"', json_str)
                            try:
                                return json.loads(fixed_str)
                            except:
                                continue # Keep searching if this chunk failed
        return None

    def _extract_entities_node(self, state: GraphState):
        safe_text = state["text"][:6000]
        
        # --- PROMPT UPDATED FOR ROBUSTNESS ---
        prompt = ChatPromptTemplate.from_template("""
            You are a strict JSON data extractor.
            
            TASK: Extract a Knowledge Graph from the text below.
            
            STRICT FORMATTING RULES:
            1. Output MUST be valid JSON.
            2. Use DOUBLE QUOTES for all keys and string values. (e.g. "key": "value").
            3. Do NOT use single quotes.
            4. Do NOT include comments // in the JSON.
            
            CONTENT RULES (Zero-Knowledge):
            1. **No Pronouns:** If text says "She", resolve it to the character name (e.g., "Little Match Girl").
            2. **Emotions:** Infer emotion ONLY from the provided text chunk. 
               - Cold/Hungry/Pain -> "Miserable"
               - Vision/Food/Warmth -> "Joyful"
            3. **Merge Names:** Use "Little Match Girl" for "child", "girl", "youngster".

            JSON STRUCTURE:
            {{
                "characters": [
                    {{ 
                        "text": "Name", 
                        "archetype": "Role", 
                        "emotion": "Adjective", 
                        "goal": "Objective" 
                    }}
                ],
                "locations": [ {{ "text": "Place Name", "type": "Setting" }} ],
                "events": [ {{ "text": "Event summary", "significance": "Medium" }} ],
                "relationships": []
            }}
            
            TEXT TO ANALYZE:
            {text}
        """)
        
        try:
            response = self.llm.invoke(prompt.format(
                text=safe_text, 
                active_characters=state["active_characters"]
            ))
            
            extracted = self._surgical_json_parser(response.content)
            
            if not extracted:
                # Last ditch effort: regex find
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    try:
                        extracted = json.loads(json_match.group())
                    except:
                        # Attempt to fix unquoted keys in regex match
                        fixed_str = re.sub(r'(?<!")(\b\w+\b)(?=\s*:)', r'"\1"', json_match.group())
                        extracted = json.loads(fixed_str)
                else:
                    raise ValueError("No JSON found")
            
            new_chars = [c.get('text') for c in extracted.get('characters', [])]
            updated_memory = list(set(state["active_characters"] + new_chars))[-15:] 

            return {"entities": extracted, "active_characters": updated_memory}
            
        except Exception as e:
            # Log the actual response to see why it failed (optional debugging)
            # print(f"FAIL RESP: {response.content}")
            print(f"⚠️ Extraction Skipped: {e}")
            return {
                "entities": {"characters": [], "locations": [], "relationships": []},
                "active_characters": state["active_characters"]
            }

    def _build_workflow(self):
        builder = StateGraph(GraphState)
        builder.add_node("extract", self._extract_entities_node)
        builder.set_entry_point("extract")
        builder.add_edge("extract", END)
        return builder.compile()

    async def extract(self, text: str, metadata: dict, context: list = None):
        return (await self.workflow.ainvoke({
            "text": text, "metadata": metadata, 
            "entities": {}, "active_characters": context or []
        }))["entities"]