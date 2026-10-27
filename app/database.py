from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()
