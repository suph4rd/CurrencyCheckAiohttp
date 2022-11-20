import os
import pathlib
from dotenv import load_dotenv

print(f"is_docker settings {os.environ.get('IS_DOCKER', False)}")
BASE_DIR = pathlib.Path(__file__).parent
dotenv_path = BASE_DIR.parent / "docker_settings.env" if os.environ.get("IS_DOCKER") else "local_settings.env"
load_dotenv(dotenv_path)


APP_HOST = os.getenv('APP_HOST', "127.0.0.1")
APP_PORT = os.getenv('APP_PORT', 8001)

if not os.getenv('DATABASE_URI'):
    raise ConnectionError("set environment variable DATABASE_URI or create env file "
                          "(docker_settings.env or local_settings.env, depends of the way of start)")
DATABASE_URL = os.getenv('DATABASE_URI')
DATABASE_URI_MIGRATION = os.getenv('DATABASE_URI_MIGRATION')

STATIC_PATH = BASE_DIR / "static"

