from typing import Dict

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_response import Response

from app import service


class MainPage(web.View):

    @aiohttp_jinja2.template('./app/templates/main_page.html')
    async def get(self) -> Dict:
        return {}


class AbstractBankInterface:
    handler_class: service.AbstractHandleClass = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.handler_class:
            raise ValueError("Обязательное поле handler_class не назначено")

    async def get(self) -> Response:
        raise NotImplementedError()


class AbstractBankTemplate(AbstractBankInterface):
    template: str = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.template:
            raise ValueError("Обязательное поле template не назначено")

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


class AbstractBankApi(AbstractBankInterface):
    async def get(self) -> Response:
        answer = await self.handler_class(is_api=True).get_result()
        if isinstance(answer, (dict, list)):
            return web.json_response(answer)
        return web.json_response({"message": "Не найдено"}, status=404)


class BelarusbankBankApi(AbstractBankApi, web.View):
    handler_class = service.BelarusbankHandleClass

    async def get(self) -> Response:
        """
        ---
        description: This end-point return information about currency exchange from Belarusbank api.
        tags:
        - API
        produces:
        - application/json
        responses:
            "200":
                description: successful operation. Return actual exchange courses from Belarusbank api
            "400":
                description: Bade request. (return description of problem)
            "417":
                description: source service isn't available
        """
        return await super().get()


class MyfinBankApi(AbstractBankApi, web.View):
    handler_class = service.MyfinHandleClass

    async def get(self) -> Response:
        """
        ---
        description: This end-point return information about currency exchange from Myfin.by.
        tags:
        - API
        produces:
        - application/json
        responses:
            "200":
                description: successful operation. Return actual exchange courses from Myfin.by
            "400":
                description: Bade request. (return description of problem)
            "417":
                description: source service isn't available
        """
        return await super().get()
