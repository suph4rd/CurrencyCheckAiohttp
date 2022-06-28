import time
from typing import Dict

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_response import Response

from app import service


class MainPage(web.View):

    @aiohttp_jinja2.template('./app/templates/main_page.html')
    async def get(self) -> Dict:
        return {}


class InterfaceBankTemplate:
    async def get(self) -> Response:
        raise NotImplementedError()


class BelarusbankBankTemplateView(InterfaceBankTemplate, web.View):

    async def get(self) -> Response:
        belarusbank_answer = await service.BelarusbankHandleClass().get_result()
        if isinstance(belarusbank_answer, Response):
            return belarusbank_answer
        elif isinstance(belarusbank_answer, (dict, list)):
            return aiohttp_jinja2.render_template(
                './app/templates/belarusbank/belarusbank-main-part.html',
                self.request,
                belarusbank_answer
            )
        return web.Response(status=404)
