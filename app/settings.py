import pathlib

import yaml

BASE_DIR = pathlib.Path(__file__).parent


def get_config(path: pathlib.Path):
    with open(path) as f:
        config = yaml.safe_load(f)
    return config


config_path = BASE_DIR / "config" / "app.yml"
config = get_config(config_path)

DATABASE_URL = "sqlite:///./db.sqlite3"

