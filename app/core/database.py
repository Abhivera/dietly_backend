from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, DisconnectionError
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Add connection pooling settings to prevent connection issues
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections that can be created
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Timeout for getting connection from pool
    echo=False,  # Set to True for SQL debugging
    connect_args={
        "connect_timeout": 10,  # Connection timeout
        "application_name": "dietly_backend"  # Application name for monitoring
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        # Test connection before yielding
        db.execute(text("SELECT 1"))
        yield db
    except (OperationalError, DisconnectionError) as e:
        logger.error(f"Database connection error: {e}")
        db.close()
        # Try to get a new session
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            db.execute(text("SELECT 1"))
            yield db
        except Exception as e2:
            logger.error(f"Failed to reconnect to database: {e2}")
            raise Exception("Database connection error. Please try again.")
    finally:
        db.close()