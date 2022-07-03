import os
import pathlib
from dotenv import load_dotenv

print(f"is_docker settings {os.environ.get('IS_DOCKER', False)}")
BASE_DIR = pathlib.Path(__file__).parent
dotenv_path = BASE_DIR.parent / "docker_settings.env" if os.environ.get("IS_DOCKER") else "local_settings.env"
load_dotenv(dotenv_path)


APP_HOST = os.getenv('APP_HOST', "127.0.0.1")
APP_PORT = os.getenv('APP_PORT', 8001)
DATABASE_URL = os.getenv('DATABASE_URI', 'sqlite:///./db.sqlite3')

STATIC_PATH = BASE_DIR / "static"

