from typing import List, Optional
import json
from sqlalchemy.orm import Session
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from app.models.sql import ResolvedEntity
from app.services.entity_service import EntityService

class AgentService:
    def __init__(self, db: Session, openai_api_key: str):
        self.db = db
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=openai_api_key)
        self.entity_service = EntityService(db)
        
        # Create tools with bound methods
        self.tools = [
            self._create_search_tool(),
            self._create_lineage_tool()
        ]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant for the Entity Nexus system. You have access to tools to search for corporate entities and view their lineage data. Use them to answer user questions accurately."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def search_entity_impl(self, query: str) -> str:
        # Simplified search: filtering ResolvedEntity by name
        results = self.db.query(ResolvedEntity).filter(ResolvedEntity.name.ilike(f"%{query}%")).limit(5).all()
        if not results:
            return "No entities found matching that name."
        
        output = []
        for r in results:
            output.append(f"ID: {r.id} | Name: {r.name} | Jurisdiction: {r.jurisdiction_code} | Rev: ${r.revenue_usd:,.2f}")
        return "\n".join(output)

    def get_entity_lineage_impl(self, entity_id: str) -> str:
        try:
            # We need to fetch the entity first
            entity = self.db.query(ResolvedEntity).filter(ResolvedEntity.id == entity_id).first()
            if not entity:
                return "Entity not found."
            
            # Summarize lineage from the entity's metadata
            lineage_summary = []
            if entity.lineage_metadata:
                for field, meta in entity.lineage_metadata.items():
                    lineage_summary.append(f"Field '{field}' from source '{meta.get('source')}' (Conf: {meta.get('confidence')})")
            else:
                lineage_summary.append("No lineage metadata available.")
            
            return f"Entity: {entity.name}\n" + "\n".join(lineage_summary)
        except Exception as e:
            return f"Error retrieving lineage: {str(e)}"

    def chat(self, user_input: str) -> str:
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result["output"]
        except Exception as e:
            return f"Agent Error: {str(e)}"

    def _create_search_tool(self):
        @tool("search_entity")
        def search_fn(query: str) -> str:
            """Search for companies by name. Useful to find the ID of an entity."""
            return self.search_entity_impl(query)
        return search_fn

    def _create_lineage_tool(self):
        @tool("get_entity_lineage")
        def lineage_fn(entity_id: str) -> str:
            """Get data lineage (source and confidence) for a specific entity ID."""
            return self.get_entity_lineage_impl(entity_id)
        return lineage_fn
