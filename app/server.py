import aiohttp_jinja2
import jinja2
from aiohttp import web

from app.routes import setup_routes

app = web.Application()
setup_routes(app)
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('.'))
web.run_app(app, port=8000)
