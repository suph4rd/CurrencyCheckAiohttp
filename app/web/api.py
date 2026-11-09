from aiohttp import web

from app import service
from app.web.mixins import BankContextMixin


class BankApi(BankContextMixin, web.View):
    async def get(self) -> web.Response:
        return web.json_response(await self.context(api=True))


class BelarusbankBankApi(BankApi):
    service_class = service.BelarusbankService

    async def get(self) -> web.Response:
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


class MyfinBankApi(BankApi):
    service_class = service.MyfinService

    async def get(self) -> web.Response:
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
