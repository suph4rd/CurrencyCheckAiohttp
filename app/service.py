from __future__ import annotations

import logging
import time
from typing import Optional

import aiohttp
from aiohttp import ClientConnectorError, ClientResponse, web
from aiohttp.web_response import Response

from app.exceptions import HandleError


class AbstractHandleClass:
    url = None
    start_time = None
    prefix = None

    async def _get_answer(self) -> list | dict | None | Response:
        logging.info("start getting answer")
        self.set_start_time()
        url = self._make_request()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    try:
                        answer = await self._handle_answer(response)
                    except Exception as err:
                        print(err)
                        raise HandleError

                    logging.info("answer have got")
                    return answer
            except ClientConnectorError as err:
                print(err)
                return web.json_response(
                    {"error": "Ошибка соединения!"},
                    status=417
                )
            except HandleError as err:
                return web.json_response(
                    {"error": str(err)},
                    status=400
                )

    def set_start_time(self) -> None:
        self.start_time = time.time()

    def _make_request(self) -> str:
        return self.url

    def _get_spent_time(self) -> float:
        return time.time() - self.start_time

    async def get_result(self) -> (float, Optional[dict]) | Response:
        answer = await self._get_answer()
        if isinstance(answer, Response):
            return answer
        return {
            f"{self.prefix}_answer": answer,
            f"{self.prefix}_time": self._get_spent_time(),
        }

    async def _handle_answer(self, response: ClientResponse) -> Optional[list | dict]:
        raise NotImplementedError()


class BelarusbankHandleClass(AbstractHandleClass):
    url = "https://belarusbank.by/api/kursExchange?city=%D0%9C%D0%B8%D0%BD%D1%81%D0%BA"
    prefix = "belarusbank"

    async def _handle_answer(self, response: ClientResponse) -> Optional[list | dict]:
        answer = await response.json()
        return answer
