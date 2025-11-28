from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

# Database URL - using SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./tasks.db")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# Dependency to get DB session
async def get_db():
    """
    Dependency function to get database session.
    Usage in FastAPI endpoints:

    @app.get("/tasks")
    async def get_tasks(db: AsyncSession = Depends(get_db)):
        ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
