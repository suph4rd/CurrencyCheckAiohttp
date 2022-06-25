from __future__ import annotations

import json
import time
from typing import Optional

import aiohttp


class AbstractHandleClass:
    url = None
    start_time = None
    prefix = None

    async def _get_answer(self) -> str:
        self.set_start_time()
        url = self._make_request()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                answer = await response.text()
                print(answer)
                return answer

    def set_start_time(self) -> None:
        self.start_time = time.time()

    def _make_request(self) -> str:
        return self.url

    def _get_spent_time(self) -> float:
        return time.time() - self.start_time

    async def get_result(self) -> (float, Optional[dict]):
        answer = await self._get_answer()
        return {
            f"{self.prefix}_answer": self._handle_answer(answer),
            f"{self.prefix}_time": self._get_spent_time(),
        }

    def _handle_answer(self, answer) -> Optional[list | dict]:
        raise NotImplementedError()


class BelarusbankHandleClass(AbstractHandleClass):
    url = "https://belarusbank.by/api/kursExchange?city=%D0%9C%D0%B8%D0%BD%D1%81%D0%BA"
    prefix = "belarusbank"

    def _handle_answer(self, answer) -> Optional[list | dict]:
        try:
            json_answer = json.loads(answer)
        except Exception as err:
            print(err)
            raise Exception("Ошибка распаковки ответа!")
        return json_answer
