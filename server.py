import time

import aiohttp_jinja2
import jinja2
from aiohttp import web
import service


routes = web.RouteTableDef()


app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('.'))


@routes.get('/')
@aiohttp_jinja2.template('./templates/main_page.html')
async def start(request):
    current_time = time.time()
    answer = {}

    belarusbank_dict = await service.BelarusbankHandleClass().get_result()
    answer.update(belarusbank_dict)

    load_time = time.time() - current_time
    answer.update({'load_time': load_time})

    return answer


app.add_routes(routes)
web.run_app(app, port=8000)
