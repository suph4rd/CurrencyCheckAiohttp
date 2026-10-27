import aiohttp_jinja2
import jinja2
from aiohttp import web
import logging
from aiohttp_swagger import setup_swagger

from app.routes import setup_routes
from app import settings


def start() -> web.Application:
    current_app = web.Application()
    current_app[aiohttp_jinja2.static_root_key] = "/static"
    setup_routes(current_app)
    setup_swagger(current_app)
    aiohttp_jinja2.setup(current_app, loader=jinja2.FileSystemLoader('.'))
    logging.basicConfig(level=logging.DEBUG)
    return current_app


current_app = start()


if __name__ == "__main__":
    web.run_app(current_app, port=settings.APP_PORT)
