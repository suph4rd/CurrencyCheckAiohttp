import aiohttp_jinja2
import jinja2
from aiohttp import web
import logging
from aiohttp_swagger import setup_swagger

from app.web.routes import setup_routes
from app.core import settings
from app.web.middleware import service_errors
from app.core.resources import application_resources
from app.web.middleware import language_middleware
from app.web.context_processors import template_context


def start() -> web.Application:
    current_app = web.Application(middlewares=[language_middleware, service_errors])
    current_app[aiohttp_jinja2.static_root_key] = "/static"
    current_app.cleanup_ctx.append(application_resources)
    setup_routes(current_app)
    setup_swagger(current_app)
    aiohttp_jinja2.setup(current_app, loader=jinja2.FileSystemLoader(settings.BASE_DIR / "templates"),
                         context_processors=[template_context])
    logging.basicConfig(level=logging.DEBUG)
    return current_app


current_app = start()


if __name__ == "__main__":
    web.run_app(current_app, port=settings.APP_PORT)
