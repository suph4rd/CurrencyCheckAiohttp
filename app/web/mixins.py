from aiohttp import web

from app import service
from app.core.enums import CurrencyEnum
from app.core.resources import HTTP_SESSION, REPOSITORY


class BankContextMixin:
    request: web.Request
    service_class: type[service.BaseRateService]

    async def context(self, api: bool) -> dict:
        handler = self.service_class(self.request.app[HTTP_SESSION], self.request.app[REPOSITORY])
        answer, elapsed = await handler()
        context = {f'{handler.prefix}_answer': answer, f'{handler.prefix}_time': elapsed}
        if handler.prefix == 'myfin':
            context['currency_enum'] = CurrencyEnum.get_dict() if api else CurrencyEnum
        return context
