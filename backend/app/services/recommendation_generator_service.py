"""
Recommendation Generator Service
Generates knowledge note recommendations from detected nuances
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from app.services.nuance_detector_service import Nuance
from app.services.knowledge_enrichment_service import KnowledgeEnrichmentService

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeNoteRecommendation:
    """A recommended knowledge note"""
    note_type: str
    title: str
    content: str
    severity: str
    tags: List[str]
    module_id: Optional[str]
    field_path: Optional[str]
    confidence: float
    source_document: str
    source_excerpt: str
    reasoning: str

class RecommendationGeneratorService:
    """
    Service for generating knowledge note recommendations from nuances.
    Creates structured knowledge notes with titles, content, tags, and metadata.
    """
    
    def __init__(self, enrichment_service: KnowledgeEnrichmentService = None):
        self.enrichment_service = enrichment_service
    
    def generate_recommendations(
        self,
        nuances: List[Nuance],
        source_document: str,
        entities: List = None
    ) -> List[KnowledgeNoteRecommendation]:
        """Generate knowledge note recommendations from nuances"""
        recommendations = []
        
        for nuance in nuances:
            # Generate recommendation
            rec = self._create_recommendation(nuance, source_document, entities)
            
            # Check for duplicates
            if not self._is_duplicate(rec):
                recommendations.append(rec)
        
        # Sort by confidence (highest first)
        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        
        logger.info(f"Generated {len(recommendations)} recommendations from {len(nuances)} nuances")
        return recommendations
    
    def _create_recommendation(
        self,
        nuance: Nuance,
        source_document: str,
        entities: List = None
    ) -> KnowledgeNoteRecommendation:
        """Create a knowledge note recommendation from a nuance"""
        
        # Generate title
        title = self._generate_title(nuance)
        
        # Generate content
        content = self._generate_content(nuance)
        
        # Extract tags
        tags = self._extract_tags(nuance)
        
        # Determine module
        module_id = self._determine_module(nuance, entities)
        
        # Determine field path
        field_path = self._determine_field_path(nuance, entities)
        
        # Calculate confidence
        confidence = self._calculate_confidence(nuance)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(nuance)
        
        return KnowledgeNoteRecommendation(
            note_type=nuance.type,
            title=title,
            content=content,
            severity=nuance.severity,
            tags=tags,
            module_id=module_id,
            field_path=field_path,
            confidence=confidence,
            source_document=source_document,
            source_excerpt=nuance.statement,
            reasoning=reasoning
        )
    
    def _generate_title(self, nuance: Nuance) -> str:
        """Generate a concise title for the note"""
        if nuance.type == 'comparison' and len(nuance.entities_involved) >= 2:
            # Comparison title: "X vs Y: Brief description"
            entity1 = nuance.entities_involved[0]
            entity2 = nuance.entities_involved[1]
            return f"{entity1} vs {entity2}: {nuance.explanation[:50]}"
        
        elif nuance.type == 'gotcha':
            # Gotcha title: "Entity: Pitfall description"
            if nuance.entities_involved:
                entity = nuance.entities_involved[0]
                return f"{entity}: {nuance.explanation[:60]}"
            else:
                return f"Gotcha: {nuance.explanation[:60]}"
        
        elif nuance.type == 'best_practice':
            # Best practice title: "Entity: Best practice"
            if nuance.entities_involved:
                entity = nuance.entities_involved[0]
                return f"{entity}: {nuance.explanation[:60]}"
            else:
                return f"Best Practice: {nuance.explanation[:60]}"
        
        else:
            # General nuance title
            if nuance.entities_involved:
                entity = nuance.entities_involved[0]
                return f"{entity}: {nuance.explanation[:60]}"
            else:
                return nuance.explanation[:70]
    
    def _generate_content(self, nuance: Nuance) -> str:
        """Generate detailed content for the note"""
        content = f"**{nuance.explanation}**\n\n"
        
        if nuance.type == 'comparison':
            content += self._generate_comparison_content(nuance)
        elif nuance.type == 'gotcha':
            content += self._generate_gotcha_content(nuance)
        elif nuance.type == 'best_practice':
            content += self._generate_best_practice_content(nuance)
        else:
            content += self._generate_general_content(nuance)
        
        # Add source statement
        content += f"\n\n**Source:**\n> {nuance.statement}"
        
        return content
    
    def _generate_comparison_content(self, nuance: Nuance) -> str:
        """Generate content for comparison notes"""
        if len(nuance.entities_involved) >= 2:
            entity1 = nuance.entities_involved[0]
            entity2 = nuance.entities_involved[1]
            
            return f"""**Key Difference:**

**{entity1}:**
- {nuance.statement.split('but')[0].strip() if 'but' in nuance.statement else 'See source statement'}

**{entity2}:**
- {nuance.statement.split('but')[1].strip() if 'but' in nuance.statement else 'See source statement'}

**When this matters:**
- Consider the differences when choosing between {entity1} and {entity2}
"""
        else:
            return nuance.statement
    
    def _generate_gotcha_content(self, nuance: Nuance) -> str:
        """Generate content for gotcha notes"""
        return f"""**⚠️ Common Pitfall:**

{nuance.statement}

**Why this matters:**
{nuance.explanation}

**Recommendation:**
- Be aware of this when working with {', '.join(nuance.entities_involved) if nuance.entities_involved else 'this feature'}
"""
    
    def _generate_best_practice_content(self, nuance: Nuance) -> str:
        """Generate content for best practice notes"""
        return f"""**✅ Recommended Approach:**

{nuance.statement}

**Benefits:**
{nuance.explanation}

**When to apply:**
- Use this approach when working with {', '.join(nuance.entities_involved) if nuance.entities_involved else 'this feature'}
"""
    
    def _generate_general_content(self, nuance: Nuance) -> str:
        """Generate content for general nuance notes"""
        return f"""**Important Detail:**

{nuance.statement}

**Context:**
{nuance.explanation}
"""
    
    def _extract_tags(self, nuance: Nuance) -> List[str]:
        """Extract relevant tags from nuance"""
        tags = set()
        
        # Add entities as tags
        for entity in nuance.entities_involved:
            tags.add(entity.lower())
        
        # Add type-specific tags
        if nuance.type == 'comparison':
            tags.add('comparison')
        elif nuance.type == 'gotcha':
            tags.add('gotcha')
            tags.add('pitfall')
        elif nuance.type == 'best_practice':
            tags.add('best_practice')
            tags.add('recommendation')
        
        # Add domain tags based on entities
        entity_str = ' '.join(nuance.entities_involved).lower()
        if 'ownership' in entity_str or 'beneficial' in entity_str:
            tags.add('ownership')
        if 'hierarchy' in entity_str or 'parent' in entity_str:
            tags.add('hierarchy')
        if 'financial' in entity_str or 'revenue' in entity_str:
            tags.add('financial')
        if 'duns' in entity_str:
            tags.add('duns')
        
        return list(tags)
    
    def _determine_module(self, nuance: Nuance, entities: List = None) -> Optional[str]:
        """Determine which D&B module this note relates to"""
        if not entities:
            return None
        
        # Find module entities
        module_entities = [e for e in entities if e.type == 'module']
        
        # Check if any module is mentioned in the nuance
        for entity in nuance.entities_involved:
            for mod_entity in module_entities:
                if entity.lower() in mod_entity.value.lower():
                    return mod_entity.value
        
        # Return first module if any
        if module_entities:
            return module_entities[0].value
        
        return None
    
    def _determine_field_path(self, nuance: Nuance, entities: List = None) -> Optional[str]:
        """Determine which field path this note relates to"""
        if not entities:
            return None
        
        # Find field entities
        field_entities = [e for e in entities if e.type == 'field']
        
        # Check if any field is mentioned in the nuance
        for entity in nuance.entities_involved:
            for field_entity in field_entities:
                if entity.lower() in field_entity.value.lower():
                    return field_entity.value
        
        return None
    
    def _calculate_confidence(self, nuance: Nuance) -> float:
        """Calculate confidence score for the recommendation"""
        score = nuance.confidence  # Start with nuance confidence
        
        # Boost for comparisons (usually high value)
        if nuance.type == 'comparison':
            score += 0.1
        
        # Boost for multiple entities (more context)
        if len(nuance.entities_involved) >= 2:
            score += 0.1
        
        # Boost for longer statements (more detail)
        if len(nuance.statement) > 100:
            score += 0.05
        
        # Penalty for very short statements
        if len(nuance.statement) < 30:
            score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def _generate_reasoning(self, nuance: Nuance) -> str:
        """Generate reasoning for why this recommendation was made"""
        reasons = []
        
        if nuance.type == 'comparison':
            reasons.append("Detected comparison pattern")
        elif nuance.type == 'gotcha':
            reasons.append("Detected potential pitfall")
        elif nuance.type == 'best_practice':
            reasons.append("Detected recommended practice")
        
        if len(nuance.entities_involved) >= 2:
            reasons.append(f"Involves {len(nuance.entities_involved)} entities")
        
        if nuance.confidence > 0.7:
            reasons.append("High confidence detection")
        
        return '; '.join(reasons)
    
    def _is_duplicate(self, recommendation: KnowledgeNoteRecommendation) -> bool:
        """Check if a similar note already exists"""
        if not self.enrichment_service:
            return False
        
        try:
            # Search for similar notes
            existing_notes = self.enrichment_service.search_notes(
                query=recommendation.title[:50],
                note_type=recommendation.note_type
            )
            
            # Check for exact title match
            for note in existing_notes:
                if note.title.lower() == recommendation.title.lower():
                    logger.info(f"Duplicate detected: {recommendation.title}")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            return False
