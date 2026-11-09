from aiohttp import ClientResponse

from app.core.constants import MYFIN_URL
from app.service.base import BaseRateService
from app.service.parsers import MyfinParser


class MyfinService(BaseRateService):
    url = MYFIN_URL
    prefix = "myfin"

    async def parse_response(self, response: ClientResponse) -> list[dict[str, str | None]]:
        return MyfinParser(await response.text())()
