"""
Basic Agent Service for D&B Explorer
Uses Ollama for natural language query parsing and search form prefilling
"""

import json
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Try to import ollama, but make it optional for graceful degradation
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama not installed. AI agent features will be disabled.")


class QueryIntent(BaseModel):
    """Parsed intent from natural language query"""
    entity_identifier: Optional[str] = None
    identifier_type: str = "unknown"  # duns, name, address, registration_number
    view_type: str = "hierarchy"  # hierarchy, ownership, legal, family_tree
    suggested_modules: List[str] = []
    filters: Dict = {}
    reasoning: str = ""
    confidence: float = 0.0


class BasicAgentService:
    """
    Basic AI agent for query parsing using Ollama.
    Prefills search forms based on natural language input.
    """
    
    def __init__(self, model: str = "llama3"):
        self.model = model
        self.available = OLLAMA_AVAILABLE
        
        # Module mapping for suggestions
        self.module_keywords = {
            'hierarchy': ['Standard_DB_Hierarchy_Connections', 'Standard_DB_Family_Tree'],
            'ownership': ['Standard_DB_OwnershipInsight', 'Standard_DB_Beneficial_Ownership'],
            'legal': ['Standard_DB_Legal_Events', 'Standard_DB_Principals_Contacts'],
            'financial': ['Standard_DB_Financial_Strength', 'Standard_DB_Payment_Insight'],
            'company_info': ['Standard_DB_companyinfo_L1', 'Standard_DB_companyinfo_L2'],
        }
    
    def parse_query(self, query: str) -> QueryIntent:
        """
        Parse natural language query and extract intent.
        Returns prefill data for search form.
        """
        if not self.available:
            return self._fallback_parse(query)
        
        try:
            # Create prompt for Ollama
            prompt = self._create_prompt(query)
            
            # Call Ollama
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.1,  # Low temperature for consistent parsing
                    'num_predict': 200,  # Limit response length
                }
            )
            
            # Parse response
            intent = self._parse_ollama_response(response['response'])
            
            # Add module suggestions
            intent.suggested_modules = self._suggest_modules(intent)
            
            return intent
            
        except Exception as e:
            logger.error(f"Error parsing query with Ollama: {e}")
            return self._fallback_parse(query)
    
    def _create_prompt(self, query: str) -> str:
        """Create prompt for Ollama"""
        return f"""You are a D&B data query parser. Extract structured information from the user's query.

User Query: "{query}"

Extract the following information and respond ONLY with valid JSON:
{{
    "entity_identifier": "the company name, DUNS number, or other identifier mentioned",
    "identifier_type": "duns|name|address|registration_number",
    "view_type": "hierarchy|ownership|legal|financial|company_info",
    "reasoning": "brief explanation of your interpretation",
    "confidence": 0.0-1.0
}}

Examples:
Query: "Show me the hierarchy for Apple Inc"
Response: {{"entity_identifier": "Apple Inc", "identifier_type": "name", "view_type": "hierarchy", "reasoning": "User wants to see corporate hierarchy for Apple Inc", "confidence": 0.9}}

Query: "Legal structure for DUNS 123456789"
Response: {{"entity_identifier": "123456789", "identifier_type": "duns", "view_type": "legal", "reasoning": "User wants legal structure for specific DUNS", "confidence": 0.95}}

Now parse the user's query and respond with JSON only:"""
    
    def _parse_ollama_response(self, response: str) -> QueryIntent:
        """Parse Ollama's JSON response"""
        try:
            # Extract JSON from response (sometimes Ollama adds extra text)
            response = response.strip()
            
            # Find JSON object
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                
                return QueryIntent(
                    entity_identifier=data.get('entity_identifier'),
                    identifier_type=data.get('identifier_type', 'unknown'),
                    view_type=data.get('view_type', 'hierarchy'),
                    reasoning=data.get('reasoning', ''),
                    confidence=float(data.get('confidence', 0.0))
                )
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            logger.error(f"Error parsing Ollama response: {e}")
            return QueryIntent(reasoning=f"Parse error: {e}", confidence=0.0)
    
    def _suggest_modules(self, intent: QueryIntent) -> List[str]:
        """Suggest D&B modules based on intent"""
        modules = []
        
        # Get modules for view type
        view_modules = self.module_keywords.get(intent.view_type, [])
        modules.extend(view_modules)
        
        # Always include company info for basic data
        if intent.view_type not in ['company_info']:
            modules.append('Standard_DB_companyinfo_L1')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_modules = []
        for module in modules:
            if module not in seen:
                seen.add(module)
                unique_modules.append(module)
        
        return unique_modules
    
    def _fallback_parse(self, query: str) -> QueryIntent:
        """
        Fallback parsing without Ollama.
        Uses simple keyword matching.
        """
        query_lower = query.lower()
        
        # Detect identifier type
        identifier_type = "unknown"
        entity_identifier = None
        
        # Check for DUNS
        if 'duns' in query_lower:
            identifier_type = "duns"
            # Extract numbers after 'duns'
            import re
            match = re.search(r'duns[:\s]+(\d+)', query_lower)
            if match:
                entity_identifier = match.group(1)
        
        # Check for view type
        view_type = "hierarchy"  # default
        if any(word in query_lower for word in ['ownership', 'owner', 'beneficial']):
            view_type = "ownership"
        elif any(word in query_lower for word in ['legal', 'structure', 'entity type']):
            view_type = "legal"
        elif any(word in query_lower for word in ['financial', 'revenue', 'payment']):
            view_type = "financial"
        elif any(word in query_lower for word in ['hierarchy', 'parent', 'subsidiary', 'family']):
            view_type = "hierarchy"
        
        # If no identifier found, assume the query is a company name
        if not entity_identifier:
            # Remove common words
            words_to_remove = ['show', 'me', 'the', 'for', 'of', 'hierarchy', 'ownership', 'legal', 'structure']
            words = query.split()
            entity_words = [w for w in words if w.lower() not in words_to_remove]
            if entity_words:
                entity_identifier = ' '.join(entity_words)
                identifier_type = "name"
        
        intent = QueryIntent(
            entity_identifier=entity_identifier,
            identifier_type=identifier_type,
            view_type=view_type,
            reasoning="Fallback parsing (Ollama not available)",
            confidence=0.5
        )
        
        intent.suggested_modules = self._suggest_modules(intent)
        
        return intent
    
    def check_ollama_status(self) -> Dict:
        """Check if Ollama is available and which models are installed"""
        if not self.available:
            return {
                'available': False,
                'reason': 'Ollama package not installed',
                'models': []
            }
        
        try:
            # Try to list models
            models = ollama.list()
            return {
                'available': True,
                'models': [m['name'] for m in models.get('models', [])],
                'current_model': self.model
            }
        except Exception as e:
            return {
                'available': False,
                'reason': f'Ollama service not running: {e}',
                'models': []
            }
