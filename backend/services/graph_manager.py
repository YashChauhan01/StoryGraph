# backend/services/graph_manager.py

from neo4j import GraphDatabase
import uuid

class KnowledgeGraphManager:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    async def create_event(self, event_data: dict, context: dict):
        """Create Level 1: Event node"""
        
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_event_tx,
                event_data,
                context
            )
            return result
    
    @staticmethod
    def _create_event_tx(tx, event_data, context):
        event_id = str(uuid.uuid4())
        
        query = """
        // Create Event node
        CREATE (e:Event {
            event_id: $event_id,
            text: $text,
            chapter: $chapter,
            paragraph: $paragraph,
            timestamp: datetime(),
            summary: $summary
        })
        
        // Link to current Arc
        WITH e
        MATCH (a:Arc {arc_id: $arc_id})
        CREATE (e)-[:BELONGS_TO]->(a)
        
        // Link to current Era
        WITH e
        MATCH (era:Era {era_id: $era_id})
        CREATE (e)-[:OCCURS_IN]->(era)
        
        RETURN e
        """
        
        result = tx.run(query,
            event_id=event_id,
            text=event_data['text'],
            chapter=event_data['chapter'],
            paragraph=event_data['paragraph'],
            summary=event_data.get('summary', ''),
            arc_id=context['current_arc'],
            era_id=context['current_era']
        )
        
        return result.single()[0]
    
    async def create_character(self, character_data: dict):
        """Create or update Character node"""
        
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_character_tx,
                character_data
            )
            return result
    
    @staticmethod
    def _create_character_tx(tx, character_data):
        query = """
        MERGE (c:Character {name: $name})
        ON CREATE SET
            c.character_id = $character_id,
            c.first_appearance_event = $event_id,
            c.created_at = datetime()
        ON MATCH SET
            c.last_seen_event = $event_id,
            c.updated_at = datetime()
        
        // Update attributes
        SET c.aliases = $aliases,
            c.description = $description
        
        RETURN c
        """
        
        character_id = str(uuid.uuid4())
        
        result = tx.run(query,
            name=character_data['name'],
            character_id=character_id,
            event_id=character_data['event_id'],
            aliases=character_data.get('aliases', []),
            description=character_data.get('description', '')
        )
        
        return result.single()[0]
    
    async def link_character_to_event(self, character_id: str, event_id: str, action: str):
        """Create relationship between character and event"""
        
        with self.driver.session() as session:
            query = """
            MATCH (c:Character {character_id: $character_id})
            MATCH (e:Event {event_id: $event_id})
            
            CREATE (c)-[:APPEARS_IN {
                action: $action,
                timestamp: datetime()
            }]->(e)
            
            RETURN c, e
            """
            
            session.run(query,
                character_id=character_id,
                event_id=event_id,
                action=action
            )
    
    async def create_arc(self, arc_data: dict):
        """Create Level 2: Arc node"""
        
        with self.driver.session() as session:
            query = """
            CREATE (a:Arc {
                arc_id: $arc_id,
                name: $name,
                type: $type,
                description: $description,
                status: 'active',
                started_at: datetime()
            })
            
            // Link to Era
            WITH a
            MATCH (era:Era {era_id: $era_id})
            CREATE (a)-[:PART_OF]->(era)
            
            // Link primary characters
            WITH a
            UNWIND $character_ids AS char_id
            MATCH (c:Character {character_id: char_id})
            CREATE (c)-[:PARTICIPATES_IN]->(a)
            
            RETURN a
            """
            
            arc_id = str(uuid.uuid4())
            
            result = session.run(query,
                arc_id=arc_id,
                name=arc_data['name'],
                type=arc_data.get('type', 'subplot'),
                description=arc_data.get('description', ''),
                era_id=arc_data['era_id'],
                character_ids=arc_data.get('character_ids', [])
            )
            
            return result.single()[0]
    
    async def create_era(self, era_data: dict):
        """Create Level 3: Era node"""
        
        with self.driver.session() as session:
            query = """
            CREATE (era:Era {
                era_id: $era_id,
                name: $name,
                description: $description,
                start_time: $start_time,
                world_state: $world_state,
                technology_level: $technology_level,
                political_climate: $political_climate,
                created_at: datetime()
            })
            
            RETURN era
            """
            
            era_id = str(uuid.uuid4())
            
            result = session.run(query,
                era_id=era_id,
                name=era_data['name'],
                description=era_data.get('description', ''),
                start_time=era_data.get('start_time', ''),
                world_state=era_data.get('world_state', {}),
                technology_level=era_data.get('technology_level', ''),
                political_climate=era_data.get('political_climate', '')
            )
            
            return result.single()[0]