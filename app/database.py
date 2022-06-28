import sqlalchemy as sa
from app import settings

engine = sa.create_engine(settings.DATABASE_URL)
sync_session = sa.orm.sessionmaker(engine, expire_on_commit=False)
Base = sa.orm.declarative_base()





