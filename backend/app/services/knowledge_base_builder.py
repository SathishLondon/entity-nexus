"""
Knowledge Base Builder for D&B Reference Data Assistant
Indexes all field dictionaries, modules, and sample data for RAG
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from app.services.reference_service import ReferenceService

logger = logging.getLogger(__name__)


class KnowledgeBaseBuilder:
    """
    Builds searchable knowledge base from D&B reference data.
    Indexes fields, modules, samples for RAG retrieval.
    """
    
    def __init__(self, reference_service: ReferenceService):
        self.reference_service = reference_service
        self.knowledge_base = {
            'fields': [],
            'modules': [],
            'topics': {},
            'field_index': {},
            'module_index': {}
        }
    
    def build(self) -> Dict:
        """Build complete knowledge base"""
        logger.info("Building knowledge base...")
        
        # Get all modules
        modules = self.reference_service.get_modules()
        
        for module in modules:
            module_id = module['id']
            logger.info(f"Indexing module: {module_id}")
            
            try:
                # Get dictionary (returns list of field dicts)
                fields = self.reference_service.get_data_dictionary(module_id)
                
                # Create dictionary structure
                dictionary = {
                    'fields': fields,
                    'description': f"{module.get('name', module_id)} data module"
                }
                
                # Index module
                self._index_module(module_id, module, dictionary)
                
                # Index fields
                self._index_fields(module_id, fields)
                
                # Get sample if available
                sample = self.reference_service.get_sample(module_id)
                if sample:
                    self._index_sample(module_id, sample)
                    
            except Exception as e:
                logger.warning(f"Could not index {module_id}: {e}")
                continue
        
        # Build topic mappings
        self._build_topic_mappings()
        
        logger.info(f"Knowledge base built: {len(self.knowledge_base['fields'])} fields, {len(self.knowledge_base['modules'])} modules")
        
        return self.knowledge_base
    
    def _index_module(self, module_id: str, module: Dict, dictionary: Dict):
        """Index module metadata"""
        module_entry = {
            'id': module_id,
            'name': module.get('name', module_id),
            'category': module.get('category', 'Other'),
            'description': dictionary.get('description', ''),
            'field_count': len(dictionary.get('fields', [])),
            'has_sample': self.reference_service.get_sample(module_id) is not None
        }
        
        self.knowledge_base['modules'].append(module_entry)
        self.knowledge_base['module_index'][module_id.lower()] = module_entry
    
    def _index_fields(self, module_id: str, fields: List[Dict]):
        """Index all fields from a module"""
        for field in fields:
            # Excel columns might vary, handle common field names
            field_entry = {
                'module_id': module_id,
                'path': field.get('JSON Path', field.get('path', '')),
                'name': field.get('Data Name', field.get('name', '')),
                'type': field.get('Data Type', field.get('type', '')),
                'description': field.get('Data Definition', field.get('description', '')),
                'example': field.get('example', ''),
                'required': field.get('required', False)
            }
            
            # Only index if we have at least a name
            if not field_entry['name']:
                continue
            
            self.knowledge_base['fields'].append(field_entry)
            
            # Index by field name for quick lookup
            field_name_lower = field_entry['name'].lower()
            if field_name_lower not in self.knowledge_base['field_index']:
                self.knowledge_base['field_index'][field_name_lower] = []
            self.knowledge_base['field_index'][field_name_lower].append(field_entry)
    
    def _index_sample(self, module_id: str, sample: Dict):
        """Extract additional context from sample JSON"""
        # Could extract actual values, patterns, etc.
        pass
    
    def _build_topic_mappings(self):
        """Build topic to module mappings"""
        topic_keywords = {
            'ownership': ['ownership', 'parent', 'ultimate', 'beneficial', 'stake', 'shareholder'],
            'hierarchy': ['hierarchy', 'family', 'tree', 'linkage', 'parent', 'subsidiary'],
            'financial': ['financial', 'revenue', 'income', 'payment', 'credit', 'rating'],
            'legal': ['legal', 'registration', 'entity type', 'jurisdiction', 'incorporation'],
            'contact': ['contact', 'address', 'phone', 'email', 'principal'],
            'company_info': ['company', 'business', 'name', 'duns', 'description'],
            'risk': ['risk', 'score', 'rating', 'failure', 'delinquency'],
        }
        
        for topic, keywords in topic_keywords.items():
            self.knowledge_base['topics'][topic] = []
            
            for module in self.knowledge_base['modules']:
                module_text = f"{module['id']} {module['name']} {module['description']}".lower()
                
                if any(keyword in module_text for keyword in keywords):
                    self.knowledge_base['topics'][topic].append(module['id'])
    
    def search_fields(self, query: str) -> List[Dict]:
        """Search fields by query"""
        query_lower = query.lower()
        results = []
        
        for field in self.knowledge_base['fields']:
            score = 0
            
            # Exact name match
            if query_lower == field['name'].lower():
                score += 10
            # Name contains query
            elif query_lower in field['name'].lower():
                score += 5
            # Description contains query
            elif query_lower in field['description'].lower():
                score += 2
            # Path contains query
            elif query_lower in field['path'].lower():
                score += 1
            
            if score > 0:
                results.append({**field, 'score': score})
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:10]  # Top 10 results
    
    def find_modules_by_topic(self, topic: str) -> List[str]:
        """Find modules related to a topic"""
        topic_lower = topic.lower()
        
        # Check exact topic match
        if topic_lower in self.knowledge_base['topics']:
            return self.knowledge_base['topics'][topic_lower]
        
        # Search module names and descriptions
        results = []
        for module in self.knowledge_base['modules']:
            module_text = f"{module['id']} {module['name']} {module['description']}".lower()
            if topic_lower in module_text:
                results.append(module['id'])
        
        return results
    
    def get_module_info(self, module_id: str) -> Optional[Dict]:
        """Get detailed module information"""
        return self.knowledge_base['module_index'].get(module_id.lower())
    
    def get_suggested_questions(self) -> List[str]:
        """Get list of suggested questions"""
        return [
            "Where can I find ownership information?",
            "What's the difference between DUNS and registration number?",
            "How do I get financial data?",
            "Show me all hierarchy-related endpoints",
            "What fields are available in the company info module?",
            "How do I find beneficial owners?",
            "What's the difference between parent and ultimate parent?",
            "Where can I find contact information?",
            "How do I access legal entity information?",
            "What risk scores are available?",
        ]
