import logging
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault('DATABASE_URI', 'postgresql+asyncpg://test:test@localhost/currencycheck_test')
os.environ.setdefault('DATABASE_URI_MIGRATION', 'postgresql+psycopg2://test:test@localhost/currencycheck_test')

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app import service
from app.enums import CurrencyEnum
from app.exceptions import DatabaseSaveError
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

        async def myfin(request):
            return web.Response(text=self.body, content_type='text/html')

        async def belarusbank(request):
            if self.bad_json:
                return web.Response(text='{broken', content_type='application/json')
            return web.json_response(BANK_JSON)

        upstream = web.Application()
        upstream.router.add_get('/myfin', myfin)
        upstream.router.add_get('/belarusbank', belarusbank)
        self.upstream = TestServer(upstream)
        await self.upstream.start_server()
        self.patches = [
            patch.object(service.MyfinHandleClass, 'url', str(self.upstream.make_url('/myfin'))),
            patch.object(service.BelarusbankHandleClass, 'url', str(self.upstream.make_url('/belarusbank'))),
            patch.object(service.AbstractHandleClass, '_save_answer', new_callable=AsyncMock),
        ]
        for item in self.patches:
            item.start()
        self.save = service.AbstractHandleClass._save_answer
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
                    self.assertEqual(data['currency_enum'], CurrencyEnum.get_dict())
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
            item = dict(zip(('USD_buy', 'USD_sell', 'EUR_buy', 'EUR_sell', 'RUB_buy', 'RUB_sell'), rates))
            item.update(name=name, EUR_USD_buy=None, EUR_USD_sell=None)
            expected.append(item)
        response = await self.client.get('/api/myfin-view/')
        self.assertEqual(response.status, 200)
        data = await response.json()
        self.assertEqual(data['myfin_answer'], expected)
        self.save.assert_awaited_once_with(expected)

        response = await self.client.get('/myfin-view/')
        self.assertEqual(response.status, 200)
        html = await response.text()
        for item in expected:
            self.assertIn(item['name'], html)
        self.assertEqual(html.count('Название банка:'), 3)
        for unwanted in ('EUR-&gt;USD', 'EUR->USD', 'None', 'Запись в отделение',
                         'лучший курс продажи', 'Логойский'):
            self.assertNotIn(unwanted, html)
        self.assertIn('2.948*', html)
        self.save.assert_awaited_with(expected)
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


class PersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_json_and_text_and_commit_failure(self):
        session = MagicMock()
        session.commit = AsyncMock()
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=session)
        context.__aexit__ = AsyncMock(return_value=False)
        with patch.object(service, 'async_session', return_value=context):
            handler = service.BelarusbankHandleClass()
            for answer in (BANK_JSON, {'value': 'тест'}, 'text response'):
                await handler._save_answer(answer)
                obj = session.add.call_args.args[0]
                self.assertEqual(obj.type_service, 'belarusbank')
                self.assertEqual(obj.text_answer if isinstance(answer, str) else obj.answer_json, answer)
            session.commit.side_effect = RuntimeError('database unavailable')
            with self.assertRaises(DatabaseSaveError):
                await handler._save_answer(BANK_JSON)

    def test_generator_exhaustion(self):
        self.assertEqual(list(service.MyfinHandleClass.get_generator([1, 2])), [1, 2])
