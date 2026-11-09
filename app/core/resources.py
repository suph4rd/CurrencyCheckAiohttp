from aiohttp import ClientSession, ClientTimeout, web

from app.core import settings
from app.core.constants import HTTP_CONNECT_TIMEOUT, HTTP_TOTAL_TIMEOUT
from app.db.connection import create_database
from app.db.repository import ResponseRepository

HTTP_SESSION = web.AppKey('http_session', ClientSession)
REPOSITORY = web.AppKey('repository', ResponseRepository)


async def application_resources(app: web.Application):
    engine, factory = create_database(settings.DATABASE_URL)
    try:
        app[REPOSITORY] = ResponseRepository(factory)
        timeout = ClientTimeout(total=HTTP_TOTAL_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
        async with ClientSession(timeout=timeout) as session:
            # aiohttp 3.14.5 has no public switch for retrying stale pooled connections.
            session._retry_connection = False
            app[HTTP_SESSION] = session
            yield
    finally:
        await engine.dispose()
