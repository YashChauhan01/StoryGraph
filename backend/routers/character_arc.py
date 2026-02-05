import os
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from neo4j import GraphDatabase
from textblob import TextBlob
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/analytics", tags=["analytics"])

# -- 1. Data Models --
class CharacterPoint(BaseModel):
    step: int
    sentiment_score: float
    emotion: str
    goal: str
    archetype: str
    scene_description: str
    smoothed_score: float | None = None

class ArcResponse(BaseModel):
    character: str
    manuscript_id: str
    data_points: List[CharacterPoint]
    overall_sentiment: str 

# -- 2. Neo4j Helper --
class AnalyticsService:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_character_arc(self, manuscript_id: str, character_name: str) -> List[Dict]:
        """
        Fetches character data sorted by sequence_index with raw text for sentiment analysis.
        """
        query = """
        MATCH (c:NarrativeEntity {manuscript_id: $mid})-[:APPEARS_IN]->(s:Scene)
        WHERE c:Character AND toLower(c.name) CONTAINS toLower($name)
        RETURN 
            s.sequence_index AS step,
            s.description AS scene_desc,
            s.raw_text AS raw_text,
            c.emotion AS emotion,
            c.goal AS goal,
            c.archetype AS archetype
        ORDER BY s.sequence_index ASC
        """
        
        with self.driver.session() as session:
            # Clean the input name just in case
            clean_name = character_name.replace("The ", "").strip()
            result = session.run(query, name=clean_name, mid=manuscript_id)
            return [record.data() for record in result]

service = AnalyticsService()

# -- 3. The Endpoint --
@router.get("/character-arc/{manuscript_id}/{character_name}", response_model=ArcResponse)
async def get_character_arc(manuscript_id: str, character_name: str):
    # Fetch Data
    raw_data = service.get_character_arc(manuscript_id, character_name)
    
    if not raw_data:
        raise HTTPException(status_code=404, detail=f"Character '{character_name}' not found in manuscript '{manuscript_id}'.")

    processed_points = []
    scores = []

    for idx, row in enumerate(raw_data):
        # Handle Nulls safely
        emotion_text = row.get("emotion") or "Neutral"
        goal_text = row.get("goal") or "Unknown"
        archetype_text = row.get("archetype") or "Unknown"
        scene_desc = row.get("scene_desc") or "Scene details unavailable"
        raw_text = row.get("raw_text") or ""  # Get actual paragraph text
        
        # Use the sequence index from DB, or fallback to loop index
        step_val = row.get("step")
        if step_val is None:
            step_val = idx + 1

        # ANALYZE SENTIMENT FROM RAW PARAGRAPH TEXT FIRST, then scene_desc, then emotion
        # This ensures the arc changes based on story content, not static emotion labels
        if raw_text and raw_text.strip():
            analysis_text = raw_text
        elif scene_desc and scene_desc != "Scene details unavailable":
            analysis_text = scene_desc
        else:
            analysis_text = emotion_text
            
        polarity = TextBlob(analysis_text).sentiment.polarity
        
        # 2. Heuristic Boost (Crucial for "Little Match Girl" type stories)
        # TextBlob often misses context. We force it based on keywords.
        text_lower = analysis_text.lower()
        
        negative_triggers = ["misery", "freezing", "frozen", "cold", "dead", "death", "pain", "sad", "despair", "fear", "anxious", "starving", "hungry", "dark", "alone", "weeping", "cry", "suffering", "struggle", "striving", "strived"]
        positive_triggers = ["warm", "comfort", "happy", "peace", "love", "beautiful", "bright", "awed", "dream", "vision", "hope", "light", "celestial", "glory", "joy", "rejoiced"]

        if any(x in text_lower for x in negative_triggers):
            polarity = -0.8
            
        elif any(x in text_lower for x in positive_triggers):
            polarity = 0.8
            
        scores.append(polarity)
        
        # 3. Smoothing (Moving Average window of 3)
        window = scores[max(0, idx-2) : idx+1]
        smoothed = sum(window) / len(window)

        processed_points.append(CharacterPoint(
            step=step_val,
            sentiment_score=round(polarity, 2),
            smoothed_score=round(smoothed, 2),
            emotion=emotion_text,
            goal=goal_text,
            archetype=archetype_text,
            scene_description=scene_desc
        ))

    # Determine Overall Arc
    if not scores:
        arc_type = "Insufficient Data"
    else:
        start_score = scores[0]
        end_score = scores[-1]
        delta = end_score - start_score
        
        if delta > 0.4: arc_type = "Redemption / Rise"
        elif delta < -0.4: arc_type = "Tragedy / Fall"
        else: arc_type = "Steady / Flat"

    return ArcResponse(
        character=character_name,
        manuscript_id=manuscript_id,
        data_points=processed_points,
        overall_sentiment=arc_type
    )