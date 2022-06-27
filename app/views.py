import time
from typing import Dict

import aiohttp_jinja2
from aiohttp import web

from app import service


class MainPage(web.View):

    @aiohttp_jinja2.template('./app/templates/main_page.html')
    async def get(self) -> Dict:
        return {}


class InterfaceBankTemplate:
    async def get(self) -> dict:
        raise NotImplementedError()


class BelarusbankBankTemplateView(InterfaceBankTemplate, web.View):

    @aiohttp_jinja2.template('./app/templates/belarusbank/belarusbank-main-part.html')
    async def get(self) -> dict:
        belarusbank_dict = await service.BelarusbankHandleClass().get_result()
        return belarusbank_dict
