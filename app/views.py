import time
from typing import Dict

import aiohttp_jinja2
from aiohttp import web

from app import service


class MainPage(web.View):

    @aiohttp_jinja2.template('./app/templates/main_page.html')
    async def get(self) -> Dict:
        current_time = time.time()
        answer = {}

        belarusbank_dict = await service.BelarusbankHandleClass().get_result()
        answer.update(belarusbank_dict)

        load_time = time.time() - current_time
        answer.update({'load_time': load_time})

        return answer
