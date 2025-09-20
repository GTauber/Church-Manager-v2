"""
Database configuration and session management for Church Manager v4.

This module sets up async SQLAlchemy with PostgreSQL for database operations.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
# Base is imported from models.base, not created here
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DATABASE_USER = os.getenv("POSTGRES_USER", "church_manager")
DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD", "church")
DATABASE_HOST = os.getenv("POSTGRES_HOST", "localhost")
DATABASE_PORT = os.getenv("POSTGRES_PORT", "5432")
DATABASE_NAME = os.getenv("POSTGRES_DB", "church_schedule_db")

# Construct database URL
DATABASE_URL = (
    f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
# Base is imported from models.base
from app.models.base import Base


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.
    
    Yields:
        AsyncSession: Database session for async operations
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """
    Initialize database tables.
    
    This function creates all tables defined in the models.
    Should be called on application startup in development.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with Base
        from app.models import (
            User,
            Ministry,
            UserMinistry,
            Schedule,
            ScheduleOccurrence,
            ScheduleAssignment,
        )
        
        await conn.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """
    Close database connections.
    
    Should be called on application shutdown.
    """
    await engine.dispose()