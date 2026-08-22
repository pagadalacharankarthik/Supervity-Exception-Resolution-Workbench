import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
engine = None

if db_url.startswith("postgresql"):
    try:
        logger.info(f"Attempting to connect to PostgreSQL at {db_url.split('@')[-1]}...")
        # Check connection with a short timeout (3 seconds)
        engine = create_engine(db_url, connect_args={"connect_timeout": 3})
        conn = engine.connect()
        conn.close()
        logger.info("Successfully connected to PostgreSQL database!")
    except Exception as e:
        logger.warning(
            f"PostgreSQL connection failed: {e}. "
            "Falling back to local SQLite file database: sqlite:///./app.db"
        )
        db_url = "sqlite:///./app.db"
        engine = None

if engine is None:
    # Initialize local SQLite fallback
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args)
    logger.info("SQLite fallback engine initialized.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
