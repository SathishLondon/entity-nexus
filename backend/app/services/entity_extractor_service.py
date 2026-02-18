"""
Entity Extractor Service
Identifies D&B modules, fields, and technical terms in text
"""

import re
from typing import List, Set, Dict, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExtractedEntity:
    """An entity extracted from text"""
    type: str  # module, field, term, endpoint
    value: str
    position: Tuple[int, int]  # (start, end) character positions
    context: str  # Surrounding text

class EntityExtractorService:
    """
    Service for extracting D&B and Entity Nexus entities from text.
    Identifies modules, fields, API endpoints, and technical terms.
    """
    
    def __init__(self, knowledge_base: Dict = None):
        self.kb = knowledge_base or {}
        self.module_pattern = self._build_module_pattern()
        self.field_pattern = self._build_field_pattern()
        self.endpoint_pattern = self._build_endpoint_pattern()
        self.technical_terms = self._load_technical_terms()
    
    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract all entities from text"""
        entities = []
        
        # Extract modules
        entities.extend(self._extract_modules(text))
        
        # Extract field paths
        entities.extend(self._extract_fields(text))
        
        # Extract API endpoints
        entities.extend(self._extract_endpoints(text))
        
        # Extract technical terms
        entities.extend(self._extract_terms(text))
        
        # Remove duplicates and sort by position
        entities = self._deduplicate(entities)
        entities.sort(key=lambda e: e.position[0])
        
        return entities
    
    def _extract_modules(self, text: str) -> List[ExtractedEntity]:
        """Extract D&B module names"""
        entities = []
        
        if self.module_pattern:
            for match in re.finditer(self.module_pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    type='module',
                    value=match.group(0),
                    position=match.span(),
                    context=self._get_context(text, match.span())
                ))
        
        return entities
    
    def _extract_fields(self, text: str) -> List[ExtractedEntity]:
        """Extract field paths (e.g., organization.duns)"""
        entities = []
        
        # Pattern for field paths: word.word or word.word.word
        field_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\b'
        
        for match in re.finditer(field_pattern, text):
            field_path = match.group(1)
            
            # Filter out common false positives
            if not self._is_likely_field_path(field_path):
                continue
            
            entities.append(ExtractedEntity(
                type='field',
                value=field_path,
                position=match.span(),
                context=self._get_context(text, match.span())
            ))
        
        return entities
    
    def _extract_endpoints(self, text: str) -> List[ExtractedEntity]:
        """Extract API endpoints"""
        entities = []
        
        if self.endpoint_pattern:
            for match in re.finditer(self.endpoint_pattern, text):
                entities.append(ExtractedEntity(
                    type='endpoint',
                    value=match.group(0),
                    position=match.span(),
                    context=self._get_context(text, match.span())
                ))
        
        return entities
    
    def _extract_terms(self, text: str) -> List[ExtractedEntity]:
        """Extract technical terms"""
        entities = []
        
        for term in self.technical_terms:
            # Case-insensitive word boundary search
            pattern = r'\b' + re.escape(term) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    type='term',
                    value=match.group(0),
                    position=match.span(),
                    context=self._get_context(text, match.span())
                ))
        
        return entities
    
    def _build_module_pattern(self) -> str:
        """Build regex pattern for module names"""
        if not self.kb or 'modules' not in self.kb:
            # Default pattern for common D&B module naming
            return r'\b(Standard_DB_\w+|Side_DB_\w+|cmp\w{3,})\b'
        
        module_ids = [m['id'] for m in self.kb['modules']]
        if not module_ids:
            return r'\b(Standard_DB_\w+|Side_DB_\w+|cmp\w{3,})\b'
        
        # Escape special regex characters and join
        escaped = [re.escape(m) for m in module_ids]
        return r'\b(' + '|'.join(escaped) + r')\b'
    
    def _build_field_pattern(self) -> str:
        """Build regex pattern for field paths"""
        # Generic pattern for dotted paths
        return r'\b([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\b'
    
    def _build_endpoint_pattern(self) -> str:
        """Build regex pattern for API endpoints"""
        return r'/api/v\d+/[\w/\-{}]+'
    
    def _load_technical_terms(self) -> Set[str]:
        """Load technical terms glossary"""
        return {
            # D&B specific
            'DUNS', 'D-U-N-S', 'duns number',
            'beneficial owner', 'UBO', 'ultimate beneficial owner',
            'corporate beneficial owner', 'CBO',
            'parent company', 'ultimate parent', 'immediate parent',
            'subsidiary', 'headquarters',
            'reliability code', 'confidence code',
            'registration number', 'company number',
            'legal entity', 'business entity',
            
            # Entity Nexus specific
            'canonical entity', 'resolved entity', 'source payload',
            'trust matrix', 'resolution logic', 'entity resolution',
            'lineage metadata', 'data lineage',
            'Neo4j', 'PostgreSQL', 'graph database',
            'ownership percentage', 'ownership stake',
            'hierarchy', 'corporate hierarchy', 'family tree',
            
            # General technical
            'API endpoint', 'REST API', 'JSON', 'schema',
            'field path', 'data dictionary', 'module',
            'query parameter', 'response payload',
        }
    
    def _is_likely_field_path(self, path: str) -> bool:
        """Check if a dotted path is likely a field path"""
        parts = path.split('.')
        
        # Filter out common false positives
        false_positives = {
            'e.g', 'i.e', 'etc.com', 'www.', '.com', '.org', '.net',
            'Mr.', 'Mrs.', 'Dr.', 'vs.'
        }
        
        if any(fp in path.lower() for fp in false_positives):
            return False
        
        # Must have at least 2 parts
        if len(parts) < 2:
            return False
        
        # Parts should be reasonable length
        if any(len(p) > 50 for p in parts):
            return False
        
        # Common field name patterns
        common_fields = {
            'organization', 'company', 'ownership', 'financial',
            'address', 'contact', 'duns', 'name', 'id', 'type',
            'date', 'status', 'code', 'number', 'percentage'
        }
        
        # Boost confidence if contains common field names
        if any(field in path.lower() for field in common_fields):
            return True
        
        # Default: likely if it looks like a path
        return True
    
    def _get_context(self, text: str, position: Tuple[int, int], window: int = 100) -> str:
        """Get context around a position in text"""
        start = max(0, position[0] - window)
        end = min(len(text), position[1] + window)
        context = text[start:end]
        
        # Clean up context
        context = context.replace('\n', ' ').strip()
        
        return context
    
    def _deduplicate(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate entities"""
        seen = set()
        unique = []
        
        for entity in entities:
            # Create a unique key
            key = (entity.type, entity.value.lower(), entity.position)
            
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        
        return unique
