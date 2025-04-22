from app.db import SessionLocal

def get_db():
    """
    FastAPI-compatible dependency to inject DB session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()