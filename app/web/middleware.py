from aiohttp import web

from app.core.exceptions import RateServiceError
from app.core.constants import LANGUAGE_COOKIE
from app.core.i18n import translations
from app.utils.language import select_language


@web.middleware
async def service_errors(request: web.Request, handler):
    try:
        return await handler(request)
    except RateServiceError as exc:
        if request.path.startswith('/api/'):
            return web.json_response(
                {'error': {'code': exc.code, 'message': request['gettext'](exc.message)}}, status=exc.status
            )
        return web.Response(text=request['gettext'](exc.message), status=exc.status)


@web.middleware
async def language_middleware(request: web.Request, handler):
    locale = select_language(request.cookies.get(LANGUAGE_COOKIE), request.headers.get('Accept-Language', ''))
    request['locale'] = locale
    request['gettext'] = translations(locale).gettext
    http_error = None
    try:
        response = await handler(request)
    except web.HTTPException as exc:
        response = http_error = exc
    response.headers['Content-Language'] = locale
    vary = [value.strip() for value in response.headers.get('Vary', '').split(',') if value.strip()]
    for header in ('Accept-Language', 'Cookie'):
        if header.lower() not in {value.lower() for value in vary}:
            vary.append(header)
    response.headers['Vary'] = ', '.join(vary)
    if http_error is not None:
        raise http_error
    return response
