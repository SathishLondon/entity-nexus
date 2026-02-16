from neo4j import GraphDatabase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Neo4j Driver
neo4j_driver = GraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
)

# PostgreSQL Engine (SQLAlchemy)
# Ensure you have a valid Postgres URI in settings, e.g. "postgresql://user:password@localhost/entity_nexus"
# For now used default docker compose credentials
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost:5432/entity_nexus"

from app.models.sql import Base

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_graph_session():
    # Helper for Neo4j sessions
    with neo4j_driver.session() as session:
        yield session

def close_neo4j():
    neo4j_driver.close()
