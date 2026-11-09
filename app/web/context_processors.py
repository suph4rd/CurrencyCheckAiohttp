from functools import partial

from aiohttp import web

from app.utils.formatting import format_rate


def request_context(request: web.Request) -> dict:
    gettext = request['gettext']
    return {
        'locale': request['locale'], '_': gettext,
        'format_rate': partial(format_rate, locale=request['locale']),
        'client_messages': {
            'loading': gettext('Loading rates…'),
            'refreshing': gettext('Updating rates…'),
            'load_error': gettext('Could not load rates. Please try again.'),
            'refresh_error': gettext('Could not update rates. Previously loaded rates are still displayed.'),
            'retry': gettext('Try again'),
            'count': gettext('{visible} of {total} records'),
            'empty': gettext('No rates available.'),
        },
    }


async def template_context(request: web.Request) -> dict:
    return request_context(request)


