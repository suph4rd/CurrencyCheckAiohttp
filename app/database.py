from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app import settings

engine = create_engine(settings.DATABASE_URL)
sync_session = sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()





