from app.core.database import engine
from app.models.sql import Base
from sqlalchemy import text

def drop_all():
    print("Dropping all tables...")
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS resolved_entities CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS canonical_entities CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS source_payloads CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS trust_matrix CASCADE"))
            conn.commit()
        print("Tables dropped.")
    except Exception as e:
        print(f"Error dropping tables: {e}")

if __name__ == "__main__":
    drop_all()
