from app.database import Base
import sqlalchemy as sa


class Response(Base):
    __tablename__ = "response"

    id = sa.Column(sa.Integer, primary_key=True)
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now(), nullable=False)
    text_answer = sa.Column(sa.String, nullable=True)
