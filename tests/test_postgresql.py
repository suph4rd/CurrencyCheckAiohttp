import asyncio
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models, service


@unittest.skipUnless(os.getenv('TEST_DATABASE_URI') and os.getenv('TEST_DATABASE_URI_MIGRATION'),
                     'Set TEST_DATABASE_URI and TEST_DATABASE_URI_MIGRATION for a disposable database')
class PostgreSQLTests(unittest.TestCase):
    def test_migrations_and_persistence(self):
        env = dict(os.environ, DATABASE_URI=os.environ['TEST_DATABASE_URI'],
                   DATABASE_URI_MIGRATION=os.environ['TEST_DATABASE_URI_MIGRATION'])
        app_dir = Path(__file__).resolve().parents[1] / 'app'
        import sys
        command = [sys.executable, '-m', 'alembic', 'upgrade', 'head']
        offline = subprocess.run(command + ['--sql'], cwd=app_dir, env=env,
                                 check=True, capture_output=True, text=True)
        self.assertIn('CREATE TABLE response', offline.stdout)
        self.assertIn('JSONB', offline.stdout)
        for _ in range(2):
            subprocess.run(command, cwd=app_dir, env=env, check=True, capture_output=True)
        asyncio.run(self.check_persistence())

    async def check_persistence(self):
        engine = create_async_engine(os.environ['TEST_DATABASE_URI'])
        factory = async_sessionmaker(engine, expire_on_commit=False)
        payload = [{'currency': 'USD', 'name': 'Банк', 'rate': '3.25'}]
        try:
            with patch.object(service, 'async_session', factory):
                handler = service.BelarusbankHandleClass()
                await handler._save_answer(payload)
                await handler._save_answer('Текст ответа')
            async with factory() as session:
                rows = (await session.scalars(select(models.Response).order_by(models.Response.id.desc()).limit(2))).all()
                self.assertEqual(rows[0].text_answer, 'Текст ответа')
                self.assertEqual(rows[1].answer_json, payload)
                self.assertEqual(rows[1].type_service, 'belarusbank')
                self.assertIsNotNone(rows[1].created_at)
        finally:
            await engine.dispose()
