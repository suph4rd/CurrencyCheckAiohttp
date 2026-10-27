import logging
import os
import unittest
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


MYFIN_HTML = ('<table><tbody id="currency_tbody"><tr class="tr-tb">'
              '<td><span>Test Bank</span></td>'
              + ''.join(f'<td>{i}.25</td>' for i in range(8))
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
                    self.assertEqual(data['myfin_answer'][0]['EUR_USD_sell'], '7.25')
                else:
                    self.assertEqual(data['belarusbank_answer'], BANK_JSON)
        self.assertEqual(self.save.await_count, 4)

    async def test_invalid_upstream_data(self):
        for body in ('not a table', '<tbody id="currency_tbody"></tbody>',
                     '<tbody id="currency_tbody"><tr class="tr-tb"><td>x</td></tr></tbody>'):
            self.body = body
            response = await self.client.get('/api/myfin-view/')
            self.assertEqual(response.status, 400)
        self.bad_json = True
        response = await self.client.get('/api/belarusbank-view/')
        self.assertEqual(response.status, 400)
        self.save.assert_not_awaited()

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
