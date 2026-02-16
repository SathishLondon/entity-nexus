from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from app.api.endpoints import graph, ingest, entity
app.include_router(graph.router, prefix=settings.API_V1_STR, tags=["graph"])
app.include_router(ingest.router, prefix=settings.API_V1_STR, tags=["ingest"])
app.include_router(entity.router, prefix=settings.API_V1_STR, tags=["entity"])

@app.get("/")
def root():
    return {"message": "Welcome to Entity Nexus API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
