import aiohttp_jinja2
from aiohttp import web

from app import service
from app.web.mixins import BankContextMixin


@aiohttp_jinja2.template('main_page.html')
async def main_page(request: web.Request) -> dict:
    return {}


class BankTemplate(BankContextMixin, web.View):
    template: str

    async def get(self) -> web.Response:
        return aiohttp_jinja2.render_template(self.template, self.request, await self.context(api=False))


class BelarusbankBankTemplateView(BankTemplate):
    template = 'belarusbank/belarusbank-main-part.html'
    service_class = service.BelarusbankService


class MyfinBankTemplateView(BankTemplate):
    template = 'myfin/myfin-main-part.html'
    service_class = service.MyfinService
