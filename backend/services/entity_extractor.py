# backend/services/entity_extractor.py

from gliner import GLiNER
import spacy

class EntityExtractor:
    def __init__(self):
        self.gliner_model = GLiNER.from_pretrained("urchade/gliner_multi")
        self.nlp = spacy.load("en_core_web_sm")
        
        self.labels = [
            "character", "location", "object", "event",
            "time", "organization", "relationship"
        ]
    
    async def extract_entities(self, text: str, context: dict):
        """Extract entities with contextual awareness"""
        
        # GLiNER extraction
        entities = self.gliner_model.predict_entities(
            text, 
            self.labels,
            threshold=0.5
        )
        
        # spaCy linguistic analysis
        doc = self.nlp(text)
        
        # Enhance with coreference resolution
        entities_enhanced = self._resolve_coreferences(
            entities, 
            doc, 
            context
        )
        
        return self._structure_entities(entities_enhanced)
    
    def _resolve_coreferences(self, entities, doc, context):
        """Map pronouns to actual entities using context"""
        
        pronoun_map = {}
        
        for token in doc:
            if token.pos_ == "PRON":
                # Use context to resolve pronoun
                resolved = self._resolve_from_context(
                    token.text, 
                    context.get('active_characters', [])
                )
                if resolved:
                    pronoun_map[token.i] = resolved
        
        # Update entities with resolved references
        return self._apply_resolution(entities, pronoun_map)
    
    def _structure_entities(self, entities):
        """Structure extracted entities by type"""
        
        structured = {
            "characters": [],
            "locations": [],
            "objects": [],
            "events": [],
            "temporal_markers": [],
            "relationships": []
        }
        
        for entity in entities:
            entity_type = entity['label']
            structured[f"{entity_type}s"].append({
                "text": entity['text'],
                "start": entity['start'],
                "end": entity['end'],
                "confidence": entity['score']
            })
        
        return structured