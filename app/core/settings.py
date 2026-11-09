import os
import pathlib
from dotenv import load_dotenv

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
dotenv_path = BASE_DIR.parent / "docker" / "env" / ("docker_settings.env" if os.environ.get("IS_DOCKER") else "local_settings.env")
load_dotenv(dotenv_path, override=False)


APP_HOST = os.getenv('APP_HOST', "127.0.0.1")
APP_PORT = os.getenv('APP_PORT', 8001)

if not os.getenv('DATABASE_URI'):
    raise ConnectionError("set environment variable DATABASE_URI or create env file "
                          "(docker/env/docker_settings.env or docker/env/local_settings.env)")
DATABASE_URL = os.environ['DATABASE_URI']
DATABASE_URI_MIGRATION = os.getenv('DATABASE_URI_MIGRATION')

STATIC_PATH = BASE_DIR / "static"

