import os
import re
from neo4j import GraphDatabase

class GraphManager:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # PROHIBITED NAMES: If the AI outputs these, we SKIP creating the node.
        self.PRONOUN_BLACKLIST = {
            "he", "she", "it", "they", "him", "her", "his", "hers", 
            "man", "woman", "person", "someone", "nobody"
        }

    def save_extracted_entities(self, entities: dict, metadata: dict):
        with self.driver.session() as session:
            session.execute_write(self._save_transaction, entities, metadata)

    def _resolve_name(self, raw_name: str) -> str:
        """
        Master cleaning function to merge duplicates.
        """
        if not raw_name: return None
        
        # 1. Basic Cleaning
        name = raw_name.strip()
        # Remove "The" prefix (case insensitive)
        name = re.sub(r'^(The|the|A|a|An|an)\s+', '', name)
        
        # 2. Check Blacklist (Case insensitive)
        if name.lower() in self.PRONOUN_BLACKLIST:
            return None # Reject this node entirely

        # 3. Canonical Mapping (Force variations to one master name)
        # You can expand this dictionary as needed.
        aliases = {
            "little girl": "Little Match Girl",
            "girl": "Little Match Girl",
            "child": "Little Match Girl",
            "youngster": "Little Match Girl",
            "match girl": "Little Match Girl",
            "poor little girl": "Little Match Girl",
            "grandmother": "Grandmother",
            "old grandmother": "Grandmother",
            "grandma": "Grandmother"
        }
        
        # Normalize to lower case for lookup, but return Title Case
        lookup = name.lower()
        if lookup in aliases:
            return aliases[lookup]
            
        # 4. Fuzzy Fallback (e.g. if name is "Little Match Girl's Slipper")
        if "match girl" in lookup: return "Little Match Girl"
        
        return name # Return original if no rules matched

    def _save_transaction(self, tx, entities, metadata):
        mid = metadata.get("manuscript_id")
        seq_index = metadata.get("chunk_index", 0) 
        para_id = metadata.get('paragraph') 
        scene_id = f"{mid}_p{para_id}"
        raw_text = metadata.get('raw_text', '')  # Store the actual paragraph text

        # 1. CREATE SCENE
        tx.run("""
            MERGE (m:Manuscript {id: $mid})
            MERGE (s:Scene {id: $sid})
            SET s.paragraph_id = $pid, 
                s.sequence_index = $seq_idx,
                s.raw_text = $text,
                s.created_at = timestamp()
            MERGE (m)-[:CONTAINS]->(s)
        """, mid=mid, sid=scene_id, pid=str(para_id), seq_idx=seq_index, text=raw_text)

        # 2. TIMELINE LINK
        if seq_index > 0:
             tx.run("""
                MATCH (curr:Scene {id: $curr_id})
                MATCH (prev:Scene {manuscript_id: $mid, sequence_index: $prev_idx})
                MERGE (prev)-[:NEXT_SCENE]->(curr)
             """, curr_id=scene_id, mid=mid, prev_idx=seq_index - 1)

        # 3. SAVE CHARACTERS (With Resolution)
        for char in entities.get("characters", []):
            final_name = self._resolve_name(char['text'])
            
            # If name was blacklisted (returned None), SKIP IT.
            if not final_name: continue 
            
            tx.run("""
                MERGE (c:NarrativeEntity {name: $name, manuscript_id: $mid})
                SET c:Character, 
                    c.archetype = $arch,
                    c.emotion = $emo,
                    c.goal = $goal
                MERGE (c)-[:APPEARS_IN]->(s:Scene {id: $sid})
            """, 
            name=final_name, 
            mid=mid, 
            sid=scene_id, 
            arch=char.get('archetype', 'Unknown'),
            emo=char.get('emotion', 'Neutral'),
            goal=char.get('goal', 'Unknown'))

        # 4. LOCATIONS
        for loc in entities.get("locations", []):
            tx.run("""
                MERGE (l:NarrativeEntity {name: $name, manuscript_id: $mid})
                SET l:Location, l.type = $type
                MERGE (s:Scene {id: $sid})-[:SETTING_IS]->(l)
            """, name=loc['text'], mid=mid, sid=scene_id, type=loc.get('type', 'Place'))

        # 5. EVENTS
        events = entities.get("events", [])
        if events:
            tx.run("MATCH (s:Scene {id: $sid}) SET s.description = $desc", sid=scene_id, desc=events[0]['text'])
        for evt in events:
             tx.run("""
                MERGE (e:Event {description: $desc, manuscript_id: $mid, scene_id: $sid})
                MERGE (s:Scene {id: $sid})-[:INCLUDES_EVENT]->(e)
            """, desc=evt['text'], mid=mid, sid=scene_id)

        print(f"💾 Scene {seq_index} Saved: Entities Resolved.")

graph_db = GraphManager()