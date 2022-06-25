import aiohttp_jinja2
import jinja2
from aiohttp import web
import logging

from app.routes import setup_routes
from app import settings


def start():
    current_app = web.Application()
    setup_routes(current_app)
    aiohttp_jinja2.setup(current_app, loader=jinja2.FileSystemLoader('.'))
    current_app["config"] = settings.config
    logging.basicConfig(level=logging.DEBUG)
    return current_app


current_app = start()


if __name__ == "__main__":
    web.run_app(current_app, port=settings.config.get("port", 8000))
