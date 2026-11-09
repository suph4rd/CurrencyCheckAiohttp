import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Response
from app.core.exceptions import DatabaseSaveError

RateData = dict[str, Any] | list[Any] | str


class ResponseRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def save(self, answer: RateData, provider: str) -> None:
        values = {"text_answer" if isinstance(answer, str) else "answer_json": answer}
        try:
            async with self.session_factory() as session:
                session.add(Response(type_service=provider, **values))
                await session.commit()
        except SQLAlchemyError as exc:
            logging.exception("Failed to save %s response", provider)
            raise DatabaseSaveError() from exc
