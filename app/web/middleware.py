from aiohttp import web

from app.core.exceptions import RateServiceError


@web.middleware
async def service_errors(request: web.Request, handler):
    try:
        return await handler(request)
    except RateServiceError as exc:
        if request.path.startswith('/api/'):
            return web.json_response(
                {'error': {'code': exc.code, 'message': exc.message}}, status=exc.status
            )
        return web.Response(text=exc.message, status=exc.status)
