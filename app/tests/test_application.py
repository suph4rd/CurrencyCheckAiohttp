import asyncio
import logging
import os
import unittest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault('DATABASE_URI', 'postgresql+asyncpg://test:test@localhost/currencycheck_test')
os.environ.setdefault('DATABASE_URI_MIGRATION', 'postgresql+psycopg2://test:test@localhost/currencycheck_test')

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app import service
from app.core.enums import CurrencyEnum
from app.core.i18n import translations
from app.core.exceptions import DatabaseSaveError
from app.db.repository import ResponseRepository
from app.core.resources import HTTP_SESSION
from sqlalchemy.exc import SQLAlchemyError
from app.server import start

logging.getLogger().setLevel(logging.CRITICAL)


MYFIN_HTML = ('<table class="currencies-courses--bordered"><tbody class="sort_body">'
              '<tr class="currencies-courses__row-main" data-row-type="default">'
              '<td><span>Test Bank</span></td>'
              + ''.join(f'<td class="currencies-courses__currency-cell">{i}.25</td>' for i in range(6))
              + '<td>extra link</td></tr></tbody></table>')
BANK_JSON = [{'filials_text': 'Test Bank', 'USD_in': '3.25'}]


class ApplicationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.body = MYFIN_HTML
        self.bad_json = False
        self.upstream_status = 200
        self.delay = 0

        async def myfin(request):
            await asyncio.sleep(self.delay)
            return web.Response(text=self.body, content_type='text/html', status=self.upstream_status)

        async def belarusbank(request):
            await asyncio.sleep(self.delay)
            if self.upstream_status != 200:
                return web.Response(status=self.upstream_status)
            if self.bad_json:
                return web.Response(text='{broken', content_type='application/json')
            return web.json_response(BANK_JSON)

        upstream = web.Application()
        upstream.router.add_get('/myfin', myfin)
        upstream.router.add_get('/belarusbank', belarusbank)
        self.upstream = TestServer(upstream)
        await self.upstream.start_server()
        self.patches = [
            patch.object(service.MyfinService, 'url', str(self.upstream.make_url('/myfin'))),
            patch.object(service.BelarusbankService, 'url', str(self.upstream.make_url('/belarusbank'))),
            patch.object(ResponseRepository, 'save', new_callable=AsyncMock),
        ]
        for item in self.patches:
            item.start()
        self.save = ResponseRepository.save
        self.client = TestClient(TestServer(start()))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        await self.upstream.close()
        for item in reversed(self.patches):
            item.stop()

    async def test_main_static_and_swagger(self):
        for path, expected in [('/', 'Курсы валют'),
                               ('/static/css/comon_styles.css', None),
                               ('/api/doc', 'swagger')]:
            with self.subTest(path=path):
                response = await self.client.get(path)
                self.assertEqual(response.status, 200)
                if expected:
                    self.assertIn(expected, await response.text())
        response = await self.client.get('/api/doc/swagger.json')
        self.assertEqual(response.status, 200)
        schema = await response.json()
        for provider in ('myfin', 'belarusbank'):
            self.assertIn('get', schema['paths'][f'/api/{provider}-view/'])
        response = await self.client.get('/api/doc/swagger_static/css/screen.css')
        self.assertEqual(response.status, 200)

    async def test_currency_labels_are_request_local(self):
        async def check(locale):
            response = await self.client.get('/api/myfin-view/',
                                             headers={'Accept-Language': locale})
            self.assertEqual(response.status, 200)
            payload = await response.json()
            expected = {}
            for key, currency in (('USD', 'USD'), ('EUR', 'EUR'),
                                  ('RUB', '100RUB'), ('EUR_USD', 'EUR->USD')):
                for side, english, russian in (('buy', 'Buy', 'Покупка'),
                                               ('sell', 'Sell', 'Продажа')):
                    expected[f'{key}_{side}'] = f'{currency} {russian if locale == "ru" else english}'
            self.assertEqual(payload['currency_enum'], expected)
            self.assertEqual(payload['myfin_answer'][0]['USD_buy'], '0.25')
            self.assertEqual(response.headers['Content-Language'], locale)
        await asyncio.gather(*(check(locale) for locale in ['ru', 'en'] * 5))

    async def test_missing_bank_name_is_localized_only_for_response(self):
        self.body = MYFIN_HTML.replace('<span>Test Bank</span>', '<span></span>')
        for locale, name in (('ru', 'Безымянный'), ('en', 'Unnamed')):
            for path in ('/api/myfin-view/', '/myfin-view/'):
                with self.subTest(locale=locale, path=path):
                    response = await self.client.get(path, headers={'Accept-Language': locale})
                    self.assertEqual(response.status, 200)
                    if path.startswith('/api/'):
                        payload = await response.json()
                        self.assertEqual(payload['myfin_answer'][0]['name'], name)
                    else:
                        self.assertIn(name, await response.text())
                    self.assertEqual(self.save.await_args.args[0][0]['name'], '')

    async def test_fragments_and_api(self):
        for provider in ('myfin', 'belarusbank'):
            with self.subTest(provider=provider):
                response = await self.client.get(f'/{provider}-view/')
                self.assertEqual(response.status, 200)
                self.assertIn('Test Bank', await response.text())
                response = await self.client.get(f'/api/{provider}-view/')
                self.assertEqual(response.status, 200)
                data = await response.json()
                self.assertIsInstance(data[f'{provider}_time'], float)
                if provider == 'myfin':
                    self.assertEqual(data['currency_enum'], CurrencyEnum.get_dict(translations("ru").gettext))
                    self.assertEqual(data['myfin_answer'][0]['RUB_sell'], '5.25')
                    self.assertIsNone(data['myfin_answer'][0]['EUR_USD_buy'])
                    self.assertIsNone(data['myfin_answer'][0]['EUR_USD_sell'])
                else:
                    self.assertEqual(data['belarusbank_answer'], BANK_JSON)
        self.assertEqual(self.save.await_count, 4)

    async def test_invalid_upstream_data(self):
        for body in ('not a table',
                     '<table class="currencies-courses--bordered"><tbody class="sort_body"></tbody></table>',
                     MYFIN_HTML.replace('<td class="currencies-courses__currency-cell">0.25</td>', ''),
                     MYFIN_HTML.replace('0.25', '')):
            self.body = body
            for path in ('/myfin-view/', '/api/myfin-view/'):
                response = await self.client.get(path)
                self.assertEqual(response.status, 400)
        self.bad_json = True
        response = await self.client.get('/api/belarusbank-view/')
        self.assertEqual(response.status, 400)
        self.save.assert_not_awaited()

    async def test_current_myfin_snapshot(self):
        self.body = (Path(__file__).parent / 'fixtures' / 'myfin_current.html').read_text(encoding='utf-8')
        expected = []
        for name, rates in (
            ('Альфа Банк', ('2.935', '2.97', '3.27', '3.3', '3.4767', '3.665')),
            ('Банк БелВЭБ', ('2.92', '2.965', '3.25', '3.35', '3.46', '3.68')),
            ('СтатусБанк', ('2.948*', '2.948', '3.282', '3.282', '3.4767', '3.625')),
        ):
            item = {key: value for key, value in zip(
                ('USD_buy', 'USD_sell', 'EUR_buy', 'EUR_sell', 'RUB_buy', 'RUB_sell'), rates)}
            item.update(name=name, EUR_USD_buy=None, EUR_USD_sell=None)
            expected.append(item)
        response = await self.client.get('/api/myfin-view/')
        self.assertEqual(response.status, 200)
        data = await response.json()
        self.assertEqual(data['myfin_answer'], expected)
        self.save.assert_awaited_once_with(expected, "myfin")

        response = await self.client.get('/myfin-view/')
        self.assertEqual(response.status, 200)
        html = await response.text()
        for item in expected:
            self.assertIn(item['name'], html)
        self.assertEqual(html.count('data-bank-name='), 3)
        self.assertIn('scope="colgroup"', html)
        for unwanted in ('EUR-&gt;USD', 'EUR->USD', 'None', 'Запись в отделение',
                         'лучший курс продажи', 'Логойский'):
            self.assertNotIn(unwanted, html)
        self.assertIn('2,948*', html)
        self.save.assert_awaited_with(expected, "myfin")
        self.assertEqual(self.save.await_count, 2)

    async def test_provider_connection_failure(self):
        await self.upstream.close()
        for provider in ('myfin', 'belarusbank'):
            response = await self.client.get(f'/api/{provider}-view/')
            self.assertEqual(response.status, 417)
        self.save.assert_not_awaited()

    async def test_database_failure(self):
        self.save.side_effect = DatabaseSaveError
        for provider in ('myfin', 'belarusbank'):
            response = await self.client.get(f'/api/{provider}-view/')
            self.assertEqual(response.status, 400)

    async def test_templates_from_another_working_directory(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                for path in ('/', '/myfin-view/', '/belarusbank-view/'):
                    response = await self.client.get(path)
                    self.assertEqual(response.status, 200)
                    html = await response.text()
                    if path == '/myfin-view/':
                        for label in ('USD', 'EUR', '100 RUB', 'Покупка', 'Продажа'):
                            self.assertIn(label, html)
            finally:
                os.chdir(previous)

    async def test_http_failure_and_error_contract(self):
        self.upstream_status = 503
        for provider in ('myfin', 'belarusbank'):
            for api in (False, True):
                response = await self.client.get(f"{'/api' if api else ''}/{provider}-view/")
                self.assertEqual(response.status, 417)
                if api:
                    self.assertEqual(await response.json(), {'error': {
                        'code': 'provider_unavailable', 'message': 'Ошибка подключения к серверу!'}})
                else:
                    self.assertEqual(await response.text(), 'Ошибка подключения к серверу!')
        self.save.assert_not_awaited()

    async def test_timeout(self):
        self.delay = 0.05
        with patch('app.core.resources.HTTP_TOTAL_TIMEOUT', 0.01):
            client = TestClient(TestServer(start()))
            async with client:
                for provider in ('myfin', 'belarusbank'):
                    response = await client.get(f'/api/{provider}-view/')
                    self.assertEqual(response.status, 417)
                    self.assertEqual((await response.json())['error']['code'], 'provider_timeout')
        self.save.assert_not_awaited()

    async def test_session_reuse_and_cleanup(self):
        from app.core import resources
        from app.core.resources import REPOSITORY
        from aiohttp import ClientSession
        engine = MagicMock()
        engine.dispose = AsyncMock()
        with patch.object(resources, 'create_database', return_value=(engine, MagicMock())):
            client = TestClient(TestServer(start()))
            await client.start_server()
            session = client.app[HTTP_SESSION]
            repository = client.app[REPOSITORY]
            self.assertIsInstance(session, ClientSession)
            self.assertEqual(session.timeout.total, 15)
            self.assertEqual(session.timeout.connect, 5)
            self.assertFalse(session._retry_connection)
            for provider in ('myfin', 'belarusbank'):
                response = await client.get(f'/api/{provider}-view/')
                self.assertEqual(response.status, 200)
                self.assertIs(client.app[HTTP_SESSION], session)
                self.assertIs(client.app[REPOSITORY], repository)
            await client.close()
            self.assertTrue(session.closed)
            engine.dispose.assert_awaited_once()

    async def test_timing_includes_save(self):
        async def save(*args):
            await asyncio.sleep(0.02)
        self.save.side_effect = save
        response = await self.client.get('/api/myfin-view/')
        self.assertGreaterEqual((await response.json())['myfin_time'], 0.02)

    async def test_error_codes(self):
        self.body = 'broken'
        response = await self.client.get('/api/myfin-view/')
        self.assertEqual((await response.json())['error']['code'], 'invalid_provider_response')
        self.body = MYFIN_HTML
        self.save.side_effect = DatabaseSaveError
        response = await self.client.get('/api/myfin-view/')
        self.assertEqual((await response.json())['error']['code'], 'database_save_failed')


class PersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_json_and_text_and_commit_failure(self):
        session = MagicMock()
        session.commit = AsyncMock()
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=session)
        context.__aexit__ = AsyncMock(return_value=False)
        repository = ResponseRepository(MagicMock(return_value=context))
        for answer in (BANK_JSON, {'value': 'тест'}, 'text response'):
            await repository.save(answer, 'belarusbank')
            obj = session.add.call_args.args[0]
            self.assertEqual(obj.type_service, 'belarusbank')
            self.assertEqual(obj.text_answer if isinstance(answer, str) else obj.answer_json, answer)
        self.assertEqual(session.commit.await_count, 3)
        session.commit.side_effect = SQLAlchemyError('database unavailable')
        with self.assertRaises(DatabaseSaveError) as raised:
            await repository.save(BANK_JSON, 'belarusbank')
        self.assertIsInstance(raised.exception.__cause__, SQLAlchemyError)

    async def test_programming_error_is_not_converted(self):
        repository = ResponseRepository(MagicMock(side_effect=RuntimeError('bug')))
        with self.assertRaises(RuntimeError):
            await repository.save(BANK_JSON, 'belarusbank')
