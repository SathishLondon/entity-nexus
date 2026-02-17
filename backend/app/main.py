from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from app.api.endpoints import graph, ingest, entity, agent, references, knowledge
app.include_router(graph.router, prefix=settings.API_V1_STR + "/graph", tags=["graph"])
app.include_router(ingest.router, prefix=settings.API_V1_STR + "/ingest", tags=["ingest"])
app.include_router(entity.router, prefix=settings.API_V1_STR + "/entities", tags=["entity"])
app.include_router(agent.router, prefix=settings.API_V1_STR + "/agent", tags=["agent"])
app.include_router(references.router, prefix=settings.API_V1_STR + "/references", tags=["references"])
app.include_router(knowledge.router, prefix=settings.API_V1_STR + "/knowledge", tags=["knowledge"])

@app.get("/")
def root():
    return {"message": "Welcome to Entity Nexus API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
