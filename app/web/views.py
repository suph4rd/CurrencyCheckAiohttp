import aiohttp_jinja2
from aiohttp import web

from app import service
from app.core.constants import LANGUAGE_COOKIE, SUPPORTED_LANGUAGES
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


async def set_language(request: web.Request) -> web.Response:
    data = await request.post()
    language = data.get('language')
    if language not in SUPPORTED_LANGUAGES:
        gettext = request['gettext']
        return web.Response(text=gettext('Unsupported language.'), status=400)
    response = web.HTTPSeeOther(location='/')
    response.set_cookie(LANGUAGE_COOKIE, language, max_age=365 * 24 * 60 * 60,
                        path='/', httponly=True, samesite='Lax', secure=request.secure)
    raise response
