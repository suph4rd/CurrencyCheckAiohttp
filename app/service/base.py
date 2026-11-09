import logging
from time import monotonic

from aiohttp import ClientError, ClientResponse, ClientSession, ContentTypeError

from app.db.repository import RateData, ResponseRepository
from app.core.exceptions import InvalidProviderResponse, ProviderTimeout, ProviderUnavailable


class BaseRateService:
    url: str
    prefix: str

    def __init__(self, http_session: ClientSession, repository: ResponseRepository):
        self.http_session = http_session
        self.repository = repository

    async def parse_response(self, response: ClientResponse) -> RateData:
        return await response.json()

    async def __call__(self) -> tuple[RateData, float]:
        started = monotonic()
        try:
            async with self.http_session.get(self.url) as response:
                response.raise_for_status()
                try:
                    answer = await self.parse_response(response)
                except (ValueError, UnicodeError, ContentTypeError) as exc:
                    logging.exception("Invalid %s response", self.prefix)
                    raise InvalidProviderResponse() from exc
        except TimeoutError as exc:
            logging.exception("Provider %s timed out", self.prefix)
            raise ProviderTimeout() from exc
        except ClientError as exc:
            logging.exception("Provider %s unavailable", self.prefix)
            raise ProviderUnavailable() from exc
        await self.repository.save(answer, self.prefix)
        return answer, monotonic() - started
