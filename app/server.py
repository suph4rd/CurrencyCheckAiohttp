import aiohttp_jinja2
import jinja2
from aiohttp import web
import logging

from app.routes import setup_routes
from app import settings

app = web.Application()
setup_routes(app)
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('.'))
app["config"] = settings.config
logging.basicConfig(level=logging.DEBUG)
web.run_app(app, port=8000)
