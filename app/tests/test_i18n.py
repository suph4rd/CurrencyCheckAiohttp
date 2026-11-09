import asyncio
import os
import unittest

os.environ.setdefault('DATABASE_URI', 'postgresql+asyncpg://test:test@localhost/currencycheck_test')

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.core.exceptions import (ProviderUnavailable, ProviderTimeout,
                                 InvalidProviderResponse, DatabaseSaveError)
from app.utils.formatting import format_rate
from app.utils.language import select_language
from app.server import start


class LanguageSelectionTests(unittest.TestCase):
    def test_negotiation(self):
        cases = [
            (None, '', 'ru'), ('en', 'ru', 'en'), ('ru', 'en', 'ru'),
            ('de', 'en-US,en;q=0.8,ru;q=0.5', 'en'),
            (None, 'ru;q=0.2,en-GB;q=0.9', 'en'),
            (None, 'en;q=0,ru;q=0.5', 'ru'),
            (None, 'en;q=0,en-US;q=1,ru;q=0.5', 'en'),
            (None, 'en;q=0,*;q=1', 'ru'),
            (None, 'en;q=0,ru;q=0,*;q=1', 'ru'),
            (None, 'en-US;q=0,en;q=1', 'en'),
            (None, 'en;q=bogus,ru;q=0.8', 'ru'),
            (None, 'ru;q=1.1,en;q=0.5', 'en'),
            (None, 'en;q=NaN,ru;q=0.5', 'ru'),
            (None, 'ru;q=0,*;q=0.5', 'en'),
            (None, '*;q=0,en;q=1', 'en'),
            (None, 'bad_thing,en;q=0.7', 'en'),
        ]
        for cookie, header, expected in cases:
            with self.subTest(cookie=cookie, header=header):
                self.assertEqual(select_language(cookie, header), expected)

    def test_rate_precision_and_notes(self):
        for value, russian, english in [
            ('2.948*', '2,948*', '2.948*'),
            ('3.2500 (note)', '3,2500 (note)', '3.2500 (note)'),
            ('0.00000000000000000001', '0,00000000000000000001', '0.00000000000000000001'),
            (None, '—', '—'), ('', '—', '—'),
        ]:
            self.assertEqual(format_rate(value, 'ru'), russian)
            self.assertEqual(format_rate(value, 'en'), english)


class LocalizationHTTPTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        app = start()
        app.cleanup_ctx.clear()

        async def error(request):
            await asyncio.sleep(0)
            error_class = {
                'provider_unavailable': ProviderUnavailable,
                'provider_timeout': ProviderTimeout,
                'invalid_provider_response': InvalidProviderResponse,
                'database_save_failed': DatabaseSaveError,
            }[request.query.get('code', 'provider_unavailable')]
            raise error_class()

        async def localized(request):
            await asyncio.sleep(0)
            return web.Response(text=request['gettext']('Loading rates…'))

        app.router.add_get('/api/test-error', error)
        app.router.add_get('/test-error', error)
        app.router.add_get('/test-localized', localized)
        self.client = TestClient(TestServer(app))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()

    async def test_preferences(self):
        response = await self.client.post('/preferences/language', data={'language': 'en'}, allow_redirects=False)
        self.assertEqual(response.status, 303)
        self.assertEqual(response.headers['Location'], '/')
        cookie = response.cookies['language']
        self.assertEqual(cookie.value, 'en')
        self.assertEqual(cookie['max-age'], '31536000')
        self.assertEqual(cookie['samesite'], 'Lax')
        response = await self.client.get('/', headers={'Accept-Language': 'ru'})
        self.assertEqual(response.headers['Content-Language'], 'en')
        self.assertIn('lang="en"', await response.text())
        response = await self.client.post('/preferences/language', data={'language': 'de'})
        self.assertEqual(response.status, 400)
        self.assertNotIn('Set-Cookie', response.headers)
        self.client.session.cookie_jar.clear()
        response = await self.client.post('/preferences/language', data={'language': 'de'},
                                          headers={'Accept-Language': 'ru'})
        self.assertEqual(await response.text(), 'Неподдерживаемый язык.')

    async def test_localized_error_contract_and_isolation(self):
        async def check(locale):
            response = await self.client.get('/api/test-error', headers={'Accept-Language': locale})
            self.assertEqual(response.status, 417)
            self.assertEqual(response.headers['Content-Language'], locale)
            self.assertEqual(set(response.headers['Vary'].split(', ')), {'Accept-Language', 'Cookie'})
            payload = await response.json()
            self.assertEqual(set(payload), {'error'})
            self.assertEqual(set(payload['error']), {'code', 'message'})
            self.assertEqual(payload['error']['code'], 'provider_unavailable')
            self.assertEqual(payload['error']['message'], {
                'ru': 'Ошибка подключения к серверу!',
                'en': 'Could not connect to the provider!',
            }[locale])
        await asyncio.gather(*(check(locale) for locale in ['en', 'ru'] * 5))
        response = await self.client.get('/test-error', headers={'Accept-Language': 'en'})
        self.assertEqual(await response.text(), 'Could not connect to the provider!')

    async def test_language_headers_on_http_errors(self):
        response = await self.client.get('/missing', headers={'Accept-Language': 'en'})
        self.assertEqual(response.status, 404)
        self.assertEqual(response.headers['Content-Language'], 'en')

    async def test_all_service_error_translations(self):
        for error_class, english in (
            (ProviderUnavailable, 'Could not connect to the provider!'),
            (ProviderTimeout, 'The provider request timed out!'),
            (InvalidProviderResponse, 'Invalid provider response!'),
            (DatabaseSaveError, 'Could not save data to the database!'),
        ):
            russian = {
                'provider_unavailable': 'Ошибка подключения к серверу!',
                'provider_timeout': 'Превышено время ожидания ответа сервера!',
                'invalid_provider_response': 'Ошибка распаковки ответа!',
                'database_save_failed': 'Ошибка записи объекта в базу данных!',
            }[error_class.code]
            for locale, expected in (('ru', russian), ('en', english)):
                for path in ('/api/test-error', '/test-error'):
                    with self.subTest(code=error_class.code, locale=locale, path=path):
                        response = await self.client.get(path, params={'code': error_class.code},
                                                         headers={'Accept-Language': locale})
                        self.assertEqual(response.status, error_class.status)
                        if path.startswith('/api/'):
                            self.assertEqual(await response.json(), {'error': {
                                'code': error_class.code, 'message': expected}})
                        else:
                            self.assertEqual(await response.text(), expected)
