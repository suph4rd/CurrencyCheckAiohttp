from typing import Dict

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_response import Response

from app import service


class MainPage(web.View):

    @aiohttp_jinja2.template('./app/templates/main_page.html')
    async def get(self) -> Dict:
        return {}


class AbstractBankTemplate:
    handler_class: service.AbstractHandleClass = None
    template: str = None

    async def get(self) -> Response:
        answer = await self.handler_class().get_result()
        if isinstance(answer, (dict, list)):
            return aiohttp_jinja2.render_template(
                self.template,
                self.request,
                answer
            )
        return web.Response(status=404)


class BelarusbankBankTemplateView(AbstractBankTemplate, web.View):
    template = "./app/templates/belarusbank/belarusbank-main-part.html"
    handler_class = service.BelarusbankHandleClass


class MyfinBankTemplateView(AbstractBankTemplate, web.View):
    template = "./app/templates/myfin/myfin-main-part.html"
    handler_class = service.MyfinHandleClass
