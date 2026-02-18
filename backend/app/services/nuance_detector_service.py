"""
Nuance Detector Service
LLM-powered detection of domain knowledge nuances in text
"""

import json
import logging
from typing import List, Dict
from dataclasses import dataclass, asdict
from app.services.entity_extractor_service import ExtractedEntity

logger = logging.getLogger(__name__)

# Try to import ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama not installed. Nuance detector will use pattern-based fallback.")

@dataclass
class Nuance:
    """A detected nuance in text"""
    type: str  # comparison, gotcha, best_practice, nuance
    severity: str  # info, warning, critical
    entities_involved: List[str]
    statement: str
    explanation: str
    confidence: float = 0.0

class NuanceDetectorService:
    """
    Service for detecting domain knowledge nuances in text.
    Uses LLM (Ollama) for semantic analysis with pattern-based fallback.
    """
    
    def __init__(self, model: str = "gemma3:latest"):
        self.model = model
        self.available = OLLAMA_AVAILABLE
    
    def detect_nuances(self, text: str, entities: List[ExtractedEntity]) -> List[Nuance]:
        """Detect nuances in text"""
        if self.available:
            return self._detect_with_llm(text, entities)
        else:
            return self._detect_with_patterns(text, entities)
    
    def _detect_with_llm(self, text: str, entities: List[ExtractedEntity]) -> List[Nuance]:
        """Detect nuances using LLM"""
        try:
            prompt = self._build_detection_prompt(text, entities)
            
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
                    'num_predict': 1000,
                }
            )
            
            # Parse JSON response
            nuances = self._parse_llm_response(response['response'])
            
            logger.info(f"Detected {len(nuances)} nuances using LLM")
            return nuances
            
        except Exception as e:
            logger.error(f"LLM nuance detection failed: {e}, falling back to patterns")
            return self._detect_with_patterns(text, entities)
    
    def _detect_with_patterns(self, text: str, entities: List[ExtractedEntity]) -> List[Nuance]:
        """Detect nuances using pattern matching (fallback)"""
        nuances = []
        
        # Detect comparisons
        nuances.extend(self._detect_comparisons(text, entities))
        
        # Detect gotchas
        nuances.extend(self._detect_gotchas(text, entities))
        
        # Detect best practices
        nuances.extend(self._detect_best_practices(text, entities))
        
        # Detect general nuances
        nuances.extend(self._detect_general_nuances(text, entities))
        
        logger.info(f"Detected {len(nuances)} nuances using patterns")
        return nuances
    
    def _detect_comparisons(self, text: str, entities: List[ExtractedEntity]) -> List[Nuance]:
        """Detect comparison statements"""
        import re
        nuances = []
        
        # Patterns for comparisons
        patterns = [
            r'(?:difference|distinguish) between (\w+) and (\w+)',
            r'(\w+) (?:vs|versus) (\w+)',
            r'unlike (\w+),?\s+(\w+) (?:does|shows|provides)',
            r'(\w+) (?:shows|returns|provides) .+ (?:but|while|whereas) (\w+)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity1 = match.group(1)
                entity2 = match.group(2) if match.lastindex >= 2 else None
                
                if entity2:
                    # Extract the full sentence
                    sentence = self._extract_sentence(text, match.start())
                    
                    nuances.append(Nuance(
                        type='comparison',
                        severity='warning',
                        entities_involved=[entity1, entity2],
                        statement=sentence,
                        explanation=f"Comparison between {entity1} and {entity2}",
                        confidence=0.7
                    ))
        
        return nuances
    
    def _detect_gotchas(self, text: str, entities: List[ExtractedEntity]) -> List[Nuance]:
        """Detect gotcha/pitfall statements"""
        import re
        nuances = []
        
        # Patterns for gotchas
        patterns = [
            r'(?:watch out|be careful|common mistake|pitfall|trap)',
            r"(?:don't|never|avoid) (?:forget|assume|use)",
            r'(?:can|may|will) (?:cause|lead to|result in) (?:issues|problems|errors)',
            r'(?:make sure|ensure|verify|check) (?:that|to)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                sentence = self._extract_sentence(text, match.start())
                
                # Extract entities mentioned in this sentence (optional)
                sentence_entities = [e.value for e in entities if self._in_sentence(e, sentence, text)]
                
                # Include even if no known entities — the sentence itself is the signal
                if len(sentence) > 20:
                    nuances.append(Nuance(
                        type='gotcha',
                        severity='warning',
                        entities_involved=sentence_entities,
                        statement=sentence,
                        explanation="Potential pitfall or common mistake",
                        confidence=0.6
                    ))
        
        return nuances
    
    def _detect_best_practices(self, text: str, entities: List[ExtractedEntity]) -> List[Nuance]:
        """Detect best practice statements"""
        import re
        nuances = []
        
        # Patterns for best practices
        patterns = [
            r'(?:always|should|must|recommended to) (\w+)',
            r'best (?:practice|way|approach) (?:is|for)',
            r'(?:prefer|use) (\w+) (?:over|instead of)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                sentence = self._extract_sentence(text, match.start())
                
                # Extract entities mentioned in this sentence (optional)
                sentence_entities = [e.value for e in entities if self._in_sentence(e, sentence, text)]
                
                # Include even if no known entities — the sentence itself is the signal
                if len(sentence) > 20:
                    nuances.append(Nuance(
                        type='best_practice',
                        severity='info',
                        entities_involved=sentence_entities,
                        statement=sentence,
                        explanation="Recommended best practice",
                        confidence=0.6
                    ))
        
        return nuances
    
    def _detect_general_nuances(self, text: str, entities: List[ExtractedEntity]) -> List[Nuance]:
        """Detect general nuances"""
        import re
        nuances = []
        
        # Patterns for nuances
        patterns = [
            r'(?:subtle|important|note|actually|in fact)',
            r'(?:however|but|although|though)',
            r'(?:specifically|particularly|especially)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                sentence = self._extract_sentence(text, match.start())
                
                # Extract entities mentioned in this sentence
                sentence_entities = [e.value for e in entities if self._in_sentence(e, sentence, text)]
                
                if sentence_entities and len(sentence) > 50:  # Avoid trivial statements
                    nuances.append(Nuance(
                        type='nuance',
                        severity='info',
                        entities_involved=sentence_entities,
                        statement=sentence,
                        explanation="Important detail or nuance",
                        confidence=0.5
                    ))
        
        return nuances
    
    def _build_detection_prompt(self, text: str, entities: List[ExtractedEntity]) -> str:
        """Build prompt for LLM nuance detection"""
        entity_list = '\n'.join([f"- {e.type}: {e.value}" for e in entities[:20]])  # Limit to avoid token overflow
        
        return f"""You are a domain knowledge extraction expert for D&B data and Entity Nexus systems.

Analyze this text and identify domain knowledge nuances that should be documented.

TEXT:
{text[:2000]}  

DETECTED ENTITIES:
{entity_list}

TASK:
Identify statements that represent:
1. COMPARISONS - Differences between two entities (e.g., "X vs Y", "unlike X, Y does...")
2. GOTCHAS - Common mistakes or pitfalls (e.g., "watch out", "don't forget", "can cause issues")
3. BEST_PRACTICES - Recommended approaches (e.g., "always", "should", "best way")
4. NUANCES - Subtle but important details (e.g., "actually", "important to note", "specifically")

For each nuance found, extract:
- type: comparison|gotcha|best_practice|nuance
- severity: info|warning|critical
- entities_involved: list of entity names mentioned
- statement: the exact statement (keep it concise, max 200 chars)
- explanation: why this is important (max 100 chars)

Return ONLY a JSON array of nuances. Example:
[
  {{
    "type": "comparison",
    "severity": "critical",
    "entities_involved": ["cmpbol", "cmpbos"],
    "statement": "cmpbol shows cumulative percentages but cmpbos shows pairwise",
    "explanation": "Different calculation methods affect interpretation"
  }}
]

Return empty array [] if no nuances found.
"""
    
    def _parse_llm_response(self, response: str) -> List[Nuance]:
        """Parse LLM JSON response into Nuance objects"""
        try:
            # Extract JSON from response (might have extra text)
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON array found in LLM response")
                return []
            
            data = json.loads(json_match.group(0))
            
            nuances = []
            for item in data:
                nuances.append(Nuance(
                    type=item.get('type', 'nuance'),
                    severity=item.get('severity', 'info'),
                    entities_involved=item.get('entities_involved', []),
                    statement=item.get('statement', ''),
                    explanation=item.get('explanation', ''),
                    confidence=0.8  # Higher confidence for LLM-detected nuances
                ))
            
            return nuances
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return []
    
    def _extract_sentence(self, text: str, position: int) -> str:
        """Extract the sentence containing the given position"""
        # Find sentence boundaries
        import re
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]\s+', text)
        
        # Find which sentence contains the position
        current_pos = 0
        for sentence in sentences:
            if current_pos <= position < current_pos + len(sentence):
                return sentence.strip()
            current_pos += len(sentence) + 2  # +2 for punctuation and space
        
        # Fallback: return surrounding text
        start = max(0, position - 100)
        end = min(len(text), position + 100)
        return text[start:end].strip()
    
    def _in_sentence(self, entity: ExtractedEntity, sentence: str, full_text: str) -> bool:
        """Check if entity is mentioned in the sentence"""
        return entity.value.lower() in sentence.lower()
