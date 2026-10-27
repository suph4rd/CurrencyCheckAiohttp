# CurrencyCheckAiohttp

This application get info about currency courses from different sources.

---------------------------------
# Docker startup

For development, no environment file is required:

```sh
docker compose up --build
```

The development application is available at `http://localhost:7777`.

Run `./deploy.sh` to prepare configuration, build and start the production
services. On first use, it creates an ignored `docker_settings.env` in the
repository root with a random PostgreSQL password and matching database URLs.
Existing files are preserved. Configuration setup requires Bash and OpenSSL.
Existing build
layers are reused, and changed services are recreated without removing images.
The application is available at `http://localhost:99`.

For direct Compose usage, prepare the configuration first:

```sh
bash setup_env.sh
docker compose -f docker-compose-prod.yml up -d --build
```

Edit `docker_settings.env` to use a different database. `DATABASE_URI` uses
`postgresql+asyncpg`, and `DATABASE_URI_MIGRATION` uses `postgresql+psycopg2`.
The default database hostname is `db` and its internal port is `5432`.
Keep this file: an existing PostgreSQL volume retains its original credentials,
so recreating the file does not change the database password.

For local development, run `./db_run.sh` to start the development database in
the foreground. Configure
`local_settings.env` and apply migrations before running `./start.sh`, which
starts Gunicorn at `http://localhost:8000` using the active Python environment,
or the repository's `.venv` / `venv` if no environment is active.

For the development database, use these values in the ignored `local_settings.env`:

```dotenv
DATABASE_URI=postgresql+asyncpg://test:1234@localhost:54321/currency_db
DATABASE_URI_MIGRATION=postgresql+psycopg2://test:1234@localhost:54321/currency_db
```

Run all scripts from the repository root.

## Python environment and dependencies

Use Python **3.15.2** (also recorded in `.python-version` and the Dockerfile).
Create a dedicated environment from the repository root:

```sh
python3.15 -m venv .venv
source .venv/bin/activate
python --version  # Must report 3.15.2
python -m pip install -r requirements.txt
python -m pip check
```

`requirements.in` lists direct runtime dependencies; `requirements.txt` pins the
complete resolved runtime environment. Optional DNS/charset accelerators and
unused HTTP clients have been removed. `SQLAlchemy[asyncio]` supplies greenlet;
asyncpg serves the application and psycopg2 serves Alembic. To refresh stable,
non-yanked releases, use a new Python 3.15.2 environment, then run:

```sh
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.in
python -m pip check
python -m pip list --outdated --format=json
python -m pip freeze > requirements.txt
```

Keep the `[asyncio]` extra on the SQLAlchemy entry after freezing.
Review the resolved versions and run all checks before committing the lock file.
Do not add `--pre`. Existing `asyncpg` and `async-timeout` updates are superseded
by the new resolution; modern aiohttp no longer requires async-timeout on Python 3.15.

## Tests

The tests use standard-library unittest and aiohttp test utilities, with no extra
test dependencies. Provider responses are served by an isolated local HTTP server;
normal tests do not connect to PostgreSQL or the real providers:

```sh
python -m unittest discover -s tests -v
```

To additionally test online/offline Alembic migrations, repeated `upgrade head`,
and JSONB/text persistence, explicitly configure a **disposable** PostgreSQL
instance (never production). The integration test creates the existing schema
and inserts test rows:

```sh
export TEST_DATABASE_URI=postgresql+asyncpg://test:test@localhost:5432/currencycheck_test
export TEST_DATABASE_URI_MIGRATION=postgresql+psycopg2://test:test@localhost:5432/currencycheck_test
python -m unittest discover -s tests -v
```

For regular application startup, configure `local_settings.env`, activate `.venv`,
then run `cd app && alembic upgrade head`, return to the repository root and run
`bash start.sh`. Swagger is available at `/api/doc`.
