from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Create engine with proper Railway PostgreSQL settings
engine = create_engine(
    "postgresql://postgres:SsDskQeSNPNREcOOLRqbOoZPEBxHBXuh@switchback.proxy.rlwy.net:47082/railway",
    poolclass=NullPool,  # Important for Railway
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test database connection
def test_db_connection():
    try:
        with engine.connect() as connection:
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False