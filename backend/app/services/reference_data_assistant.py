"""
Reference Data Assistant - RAG-powered AI assistant for D&B data questions
"""

import json
import logging
from typing import Dict, List, Optional
from app.services.knowledge_base_builder import KnowledgeBaseBuilder
from app.services.reference_service import ReferenceService

logger = logging.getLogger(__name__)

# Try to import ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama not installed. Assistant will use fallback mode.")


class ReferenceDataAssistant:
    """
    AI-powered assistant for answering questions about D&B reference data.
    Uses RAG (Retrieval Augmented Generation) with Ollama.
    """
    
    def __init__(self, reference_service: ReferenceService, model: str = "gemma3:latest"):
        self.reference_service = reference_service
        self.model = model
        self.available = OLLAMA_AVAILABLE
        
        # Build knowledge base
        self.kb_builder = KnowledgeBaseBuilder(reference_service)
        self.knowledge_base = self.kb_builder.build()
    
    def ask(self, question: str) -> Dict:
        """
        Answer a question about D&B reference data.
        Returns structured response with answer, examples, and actions.
        """
        logger.info(f"Question: {question}")
        
        # Retrieve relevant context
        context = self._retrieve_context(question)
        
        # Generate answer
        if self.available:
            answer = self._generate_with_ollama(question, context)
        else:
            answer = self._generate_fallback(question, context)
        
        # Build response
        response = {
            'answer': answer,
            'relevant_modules': context.get('modules', []),
            'relevant_fields': context.get('fields', []),
            'sample_json': context.get('sample_json'),
            'try_it_actions': self._generate_actions(context),
            'related_questions': self._get_related_questions(question)
        }
        
        return response
    
    def _retrieve_context(self, question: str) -> Dict:
        """Retrieve relevant context from knowledge base"""
        context = {
            'modules': [],
            'fields': [],
            'sample_json': None
        }
        
        question_lower = question.lower()
        
        # Detect topic
        topics = []
        if any(word in question_lower for word in ['ownership', 'owner', 'parent', 'beneficial']):
            topics.append('ownership')
        if any(word in question_lower for word in ['hierarchy', 'family', 'tree', 'subsidiary']):
            topics.append('hierarchy')
        if any(word in question_lower for word in ['financial', 'revenue', 'income', 'payment']):
            topics.append('financial')
        if any(word in question_lower for word in ['legal', 'registration', 'entity']):
            topics.append('legal')
        if any(word in question_lower for word in ['contact', 'address', 'phone']):
            topics.append('contact')
        if any(word in question_lower for word in ['endpoint', 'api', 'call']):
            topics.append('api')
        
        # Find relevant modules
        for topic in topics:
            module_ids = self.kb_builder.find_modules_by_topic(topic)
            for module_id in module_ids[:3]:  # Top 3 per topic
                module_info = self.kb_builder.get_module_info(module_id)
                if module_info and module_info not in context['modules']:
                    context['modules'].append(module_info)
        
        # Search fields
        field_results = self.kb_builder.search_fields(question)
        context['fields'] = field_results[:5]  # Top 5 fields
        
        # Get sample JSON from first relevant module
        if context['modules']:
            try:
                sample = self.reference_service.get_sample(context['modules'][0]['id'])
                if sample:
                    context['sample_json'] = sample
            except:
                pass
        
        return context
    
    def _generate_with_ollama(self, question: str, context: Dict) -> str:
        """Generate answer using Ollama with RAG context"""
        try:
            # Build prompt with context
            prompt = self._build_prompt(question, context)
            
            # Call Ollama
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
                    'num_predict': 500,
                }
            )
            
            return response['response'].strip()
            
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return self._generate_fallback(question, context)
    
    def _build_prompt(self, question: str, context: Dict) -> str:
        """Build prompt with retrieved context"""
        prompt = f"""You are a D&B reference data expert. Answer the user's question using the provided context.

User Question: {question}

Available Context:

"""
        
        # Add modules
        if context['modules']:
            prompt += "Relevant Modules:\n"
            for module in context['modules']:
                prompt += f"- {module['id']}: {module['description']}\n"
            prompt += "\n"
        
        # Add fields
        if context['fields']:
            prompt += "Relevant Fields:\n"
            for field in context['fields'][:3]:
                prompt += f"- {field['path']}: {field['description']}\n"
            prompt += "\n"
        
        # Add sample
        if context['sample_json']:
            prompt += f"Sample JSON:\n{json.dumps(context['sample_json'], indent=2)[:500]}...\n\n"
        
        prompt += """
Instructions:
1. Provide a clear, concise answer
2. Mention specific module names and field paths
3. Explain any nuances or differences
4. Use markdown formatting
5. Keep response under 300 words

Answer:"""
        
        return prompt
    
    def _generate_fallback(self, question: str, context: Dict) -> str:
        """Generate answer without Ollama (template-based)"""
        question_lower = question.lower()
        
        # Ownership questions
        if 'ownership' in question_lower or 'owner' in question_lower:
            return self._answer_ownership(context)
        
        # Hierarchy questions
        elif 'hierarchy' in question_lower or 'family' in question_lower:
            return self._answer_hierarchy(context)
        
        # Financial questions
        elif 'financial' in question_lower or 'revenue' in question_lower:
            return self._answer_financial(context)
        
        # DUNS questions
        elif 'duns' in question_lower:
            return self._answer_duns(context)
        
        # Endpoint questions
        elif 'endpoint' in question_lower or 'api' in question_lower:
            return self._answer_endpoints(context)
        
        # Generic answer
        else:
            return self._answer_generic(context)
    
    def _answer_ownership(self, context: Dict) -> str:
        """Answer ownership-related questions"""
        modules = [m for m in context['modules'] if 'ownership' in m['id'].lower()]
        
        answer = "**Ownership information is available in:**\n\n"
        
        for module in modules[:3]:
            answer += f"**{module['id']}**\n"
            answer += f"- {module['description']}\n"
            answer += f"- Fields: {module['field_count']}\n\n"
        
        answer += "\n**Key Nuances:**\n"
        answer += "- OwnershipInsight shows percentage stakes\n"
        answer += "- Beneficial_Ownership reveals individual owners\n"
        answer += "- Hierarchy_Connections shows the full family tree\n"
        
        return answer
    
    def _answer_hierarchy(self, context: Dict) -> str:
        """Answer hierarchy-related questions"""
        modules = [m for m in context['modules'] if 'hierarchy' in m['id'].lower() or 'family' in m['id'].lower()]
        
        answer = "**Hierarchy information is available in:**\n\n"
        
        for module in modules[:3]:
            answer += f"**{module['id']}**\n"
            answer += f"- {module['description']}\n\n"
        
        answer += "\n**API Endpoints:**\n"
        answer += "- `GET /api/v1/references/{module_id}/hierarchy` - Extract hierarchy\n"
        answer += "- `GET /api/v1/references/hierarchy/summary` - List hierarchy modules\n"
        
        return answer
    
    def _answer_financial(self, context: Dict) -> str:
        """Answer financial-related questions"""
        modules = [m for m in context['modules'] if 'financial' in m['id'].lower()]
        
        answer = "**Financial data is available in:**\n\n"
        
        for module in modules[:3]:
            answer += f"**{module['id']}**\n"
            answer += f"- {module['description']}\n\n"
        
        return answer
    
    def _answer_duns(self, context: Dict) -> str:
        """Answer DUNS-related questions"""
        return """**DUNS Number:**
- Unique 9-digit identifier assigned by D&B
- Global standard across all countries
- Never changes for an entity
- Field: `organization.duns`

**Registration Number:**
- Government-issued business registration
- Varies by jurisdiction (e.g., UK Company Number, US EIN)
- Can change if entity re-registers
- Field: `organization.registrationNumbers[]`

**When to use:**
- DUNS: For D&B API calls and cross-referencing
- Registration Number: For legal/compliance lookups
"""
    
    def _answer_endpoints(self, context: Dict) -> str:
        """Answer endpoint-related questions"""
        answer = "**Available API Endpoints:**\n\n"
        
        if context['modules']:
            module_id = context['modules'][0]['id']
            answer += f"**For {module_id}:**\n"
            answer += f"- `GET /api/v1/references/{module_id}/dictionary` - Field dictionary\n"
            answer += f"- `GET /api/v1/references/{module_id}/sample` - Sample JSON\n"
            answer += f"- `GET /api/v1/references/{module_id}/analyze` - Field analysis\n"
        
        answer += "\n**General Endpoints:**\n"
        answer += "- `GET /api/v1/references/modules` - List all modules\n"
        answer += "- `GET /api/v1/references/hierarchy/summary` - Hierarchy modules\n"
        
        return answer
    
    def _answer_generic(self, context: Dict) -> str:
        """Generic answer based on context"""
        if not context['modules']:
            return "I couldn't find specific information about that. Try asking about ownership, hierarchy, financial data, or API endpoints."
        
        answer = "**Relevant modules:**\n\n"
        for module in context['modules'][:3]:
            answer += f"**{module['id']}**\n"
            answer += f"- {module['description']}\n"
            answer += f"- {module['field_count']} fields available\n\n"
        
        return answer
    
    def _generate_actions(self, context: Dict) -> List[Dict]:
        """Generate 'Try it' actions"""
        actions = []
        
        if context['modules']:
            module_id = context['modules'][0]['id']
            actions.append({
                'label': f'View {module_id} dictionary',
                'action': 'view_dictionary',
                'params': {'module_id': module_id}
            })
            
            if context['sample_json']:
                actions.append({
                    'label': 'View sample JSON',
                    'action': 'view_sample',
                    'params': {'module_id': module_id}
                })
        
        return actions
    
    def _get_related_questions(self, question: str) -> List[str]:
        """Get related questions"""
        all_questions = self.kb_builder.get_suggested_questions()
        
        # Simple: return 3 random suggestions
        import random
        return random.sample(all_questions, min(3, len(all_questions)))
    
    def get_suggested_questions(self) -> List[str]:
        """Get list of suggested questions"""
        return self.kb_builder.get_suggested_questions()
