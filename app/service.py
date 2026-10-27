from __future__ import annotations

import logging
import time
from typing import Optional, Generator, Iterable

import aiohttp
from aiohttp import ClientConnectorError, ClientResponse, web
from aiohttp.web_exceptions import HTTPExpectationFailed
from bs4 import BeautifulSoup

from app import models
from app.database import async_session
from app.enums import CurrencyEnum
from app.exceptions import HandleError, DatabaseSaveError


class AbstractHandleClass:
    url: str = None
    start_time: time = None
    prefix: str = None
    is_api: bool = False

    def __init__(self, *args, **kwargs):
        if kwargs.get("is_api"):
            self.is_api = True

    async def _get_answer(self) -> Optional[dict | list]:
        logging.info(f"start getting answer ({self.prefix or ''})")
        self.set_start_time()
        url = self._make_request()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    try:
                        answer = await self._handle_answer(response)
                    except Exception as err:
                        logging.error(str(err))
                        raise HandleError

                    await self._save_answer(answer)
                    logging.info(f"answer have got ({self.prefix or ''})")
                    return answer
            except ClientConnectorError as err:
                logging.error(str(err))
                raise HTTPExpectationFailed(text="Ошибка подключения к серверу!")

    def set_start_time(self) -> None:
        self.start_time = time.time()

    def _make_request(self) -> str:
        return self.url

    def _get_spent_time(self) -> float:
        return time.time() - self.start_time

    async def get_result(self) -> Optional[dict]:
        answer = await self._get_answer()
        return {
            f"{self.prefix}_answer": answer,
            f"{self.prefix}_time": self._get_spent_time(),
        }

    async def _save_answer(self, answer: dict) -> None:
        try:
            async with async_session() as session:
                if isinstance(answer, (dict, list)):
                    obj = models.Response(
                        answer_json=answer, type_service=self.prefix
                    )
                elif isinstance(answer, str):
                    obj = models.Response(
                        text_answer=answer, type_service=self.prefix
                    )
                else:
                    raise DatabaseSaveError()
                session.add(obj)
                await session.commit()
                logging.info(f"saved in database ({self.prefix or ''})")
        except Exception as err:
            logging.error(str(err))
            raise DatabaseSaveError()

    async def _handle_answer(self, response: ClientResponse) -> Optional[list | dict]:
        answer = await response.json()
        return answer


class BelarusbankHandleClass(AbstractHandleClass):
    url = "https://belarusbank.by/api/kursExchange?city=%D0%9C%D0%B8%D0%BD%D1%81%D0%BA"
    prefix = "belarusbank"


class MyfinHandleClass(AbstractHandleClass):
    url = "https://myfin.by/currency/minsk"
    prefix = "myfin"

    async def _handle_answer(self, response: ClientResponse) -> Optional[list | dict]:
        answer = await response.text()
        handled_answer = self.__get_answer(answer)
        return handled_answer

    async def get_result(self) -> Optional[dict]:
        answer = await super(MyfinHandleClass, self).get_result()
        if isinstance(answer, dict):
            answer.update({"currency_enum": CurrencyEnum.get_dict() if self.is_api else CurrencyEnum})
        return answer

    @staticmethod
    def get_generator(any_iterable_obj: Iterable) -> Generator:
        for item in any_iterable_obj:
            yield item

    def __get_answer(self, answer: str) -> Optional[list]:
        handled_answer = []
        soup = BeautifulSoup(answer, 'html.parser')
        banks_body = soup.select_one("tbody#currency_tbody")
        if banks_body is None:
            raise ValueError("Myfin currency table is missing")
        banks_list_tr = banks_body.select("tr.tr-tb")
        for bank_tr in banks_list_tr:
            bank_item = {}
            cells = bank_tr.find_all("td", recursive=False)
            currency_keys = list(CurrencyEnum.__members__)
            if len(cells) < len(currency_keys) + 1:
                raise ValueError("Myfin currency row is incomplete")
            name = cells[0].find("span")
            bank_item["name"] = (name or cells[0]).get_text(strip=True) or "Безымянный"
            for key, cell in zip(currency_keys, cells[1:]):
                bank_item[key] = cell.get_text(strip=True)
            handled_answer.append(bank_item)

        if not handled_answer:
            raise ValueError("Myfin currency table is empty")
        return handled_answer

