# CurrencyCheckAiohttp

An asynchronous currency exchange rate viewer for Minsk. The application fetches
JSON from Belarusbank and parses the Myfin currency table, displays rates in a
Russian-language web interface, and exposes JSON endpoints.

Every request to a provider's HTML or JSON endpoint fetches upstream data and
saves the parsed response to PostgreSQL before returning it. There is no cache
or background polling; a working database is required to retrieve rates.

The stack uses Python **3.15.2** (specified in `build/Dockerfile`), aiohttp,
Jinja2, Beautiful Soup, asynchronous SQLAlchemy with asyncpg, Alembic with
psycopg2, and Gunicorn. Compose uses PostgreSQL 14.1; the production stack
adds Nginx.

## Quick start with Docker

Run commands from the repository root. Install Docker with Compose support.
The development stack requires no environment file:

```sh
docker compose up --build
```

Open <http://localhost:7777>. Compose waits for PostgreSQL to become healthy,
applies migrations, then starts four Gunicorn aiohttp workers. The database
is available on `localhost:54321`: database `currency_db`, user `test`,
password `1234`.

Stop the stack with Ctrl+C. To remove its containers and network:

```sh
docker compose down
```

The development database has no explicitly configured persistent volume.
Development and production both publish database port `54321`, so they cannot
use that host port simultaneously.

## Local development

Install Python 3.15.2 and create a virtual environment:

```sh
python3.15 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install -r requirements.txt
python -m pip check
```

`requirements.txt` pins runtime dependencies, including transitive dependencies.
Installing psycopg2 from source requires a C compiler and PostgreSQL development
headers, including `pg_config`.

Start only the development database in a separate terminal:

```sh
bash db_run.sh
```

Create an ignored `local_settings.env` in the repository root:

```dotenv
DATABASE_URI=postgresql+asyncpg://test:1234@localhost:54321/currency_db
DATABASE_URI_MIGRATION=postgresql+psycopg2://test:1234@localhost:54321/currency_db
```

Apply migrations and start the application:

```sh
cd app
python -m alembic upgrade head
cd ..
bash start.sh
```

Open <http://localhost:8000>. `start.sh` selects the active virtual environment,
then falls back to the repository's `.venv`, `venv`, or `python3`. It checks
application imports and starts four Gunicorn workers bound to `localhost:8000`.
It does not apply migrations.

## Production Compose stack

Prepare configuration and start PostgreSQL, the application, and Nginx:

```sh
bash deploy.sh
```

Open <http://localhost:99>. On first use, `setup_env.sh` creates an ignored
`docker_settings.env` with a random PostgreSQL password and matching database
URLs. It requires Bash and OpenSSL and preserves existing configuration.
`deploy.sh` builds and starts services, then restarts Nginx to resolve the
application container's current IP address.

For direct Compose usage:

```sh
bash setup_env.sh
docker compose -f docker-compose-prod.yml up -d --build
docker compose -f docker-compose-prod.yml restart nginx
```

Migrations run automatically before Gunicorn starts. PostgreSQL data is stored
in the named `db` volume. Keep `docker_settings.env`: regenerating credentials
does not change the password of an already initialized database volume.

Useful management commands:

```sh
docker compose -f docker-compose-prod.yml ps
docker compose -f docker-compose-prod.yml logs -f project
docker compose -f docker-compose-prod.yml down
```

`down` preserves the named database volume. Nginx serves `/static/` directly
and proxies application requests. The supplied configuration serves HTTP and
publishes PostgreSQL on host port `54321`; configure TLS and database access
restrictions for your deployment environment.

## Configuration

`app/settings.py` loads `local_settings.env` by default, or `docker_settings.env`
when `IS_DOCKER` has a nonempty value. Existing process environment variables
take precedence. Production Compose injects `docker_settings.env` through
`env_file`; development Compose supplies database URLs directly.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URI` | Required SQLAlchemy URL using `postgresql+asyncpg` for the application. |
| `DATABASE_URI_MIGRATION` | SQLAlchemy URL using `postgresql+psycopg2`, required for Alembic. |
| `IS_DOCKER` | Selects `docker_settings.env` when set to a nonempty value. |
| `APP_PORT` | Used by `python -m app.server`; defaults to `8001`. Gunicorn scripts and Compose set bind ports explicitly. |
| `APP_HOST` | Loaded by settings but currently not used to bind the server. |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Initialize production Compose PostgreSQL; must match the database URLs. |

Keep credentials in ignored environment files or process environment variables.
When using an external database, update both database URLs.

## HTTP routes and API

All routes below use `GET`:

| Route | Response |
| --- | --- |
| `/` | Main page; JavaScript loads both provider fragments. |
| `/belarusbank-view/` | Belarusbank rates as an HTML fragment. |
| `/myfin-view/` | Myfin rates as an HTML fragment. |
| `/api/belarusbank-view/` | Belarusbank rates as JSON. |
| `/api/myfin-view/` | Myfin rates as JSON, with currency label mappings. |
| `/api/doc` | Swagger UI. |
| `/api/doc/swagger.json` | Generated Swagger schema. |
| `/static/` | Bundled styles, JavaScript, and Bootstrap assets. |

For example, with development Compose running:

```sh
curl http://localhost:7777/api/belarusbank-view/
curl http://localhost:7777/api/myfin-view/
```

Belarusbank returns `belarusbank_answer` containing the provider's JSON payload
and `belarusbank_time` containing elapsed processing time in seconds. Myfin
returns `myfin_answer`, `myfin_time`, and `currency_enum`, a mapping of currency
keys to display labels. Timing includes fetching, parsing, and persistence.

Each item in `myfin_answer` contains `name`, `USD_buy`, `USD_sell`, `EUR_buy`,
`EUR_sell`, `RUB_buy`, and `RUB_sell`. Rates remain strings, preserving upstream
markers such as `*`; RUB rates are quoted per 100 RUB. `EUR_USD_buy` and
`EUR_USD_sell` are currently `null` and are omitted from the HTML display.

Implemented error responses:

| Status | Cause |
| --- | --- |
| `400` | Parsing fails, the Myfin table is missing/empty/incomplete, or saving to the database fails. |
| `417` | An upstream connection fails with aiohttp's `ClientConnectorError`. |

These exceptions return text error messages, including on JSON API routes.
Other exceptions can produce `500` responses. Myfin HTML changes may require
updating the parser in `app/service.py`.

## Persistence and project layout

The `response` table stores an ID, creation timestamp, provider name
(`type_service`), and either JSONB (`answer_json`) or text (`text_answer`).
Current provider handlers save parsed JSON-compatible data. There is no route
for reading stored history.

```text
app/
  server.py          Application initialization, Jinja2, and Swagger
  routes.py          Route registration
  views.py           HTML and JSON handlers
  service.py         Provider requests, parsing, and persistence
  settings.py        Environment configuration
  database.py        Async SQLAlchemy engine and session factory
  models.py          Response model
  enums.py           Currency keys and display labels
  exceptions.py      Parsing and persistence HTTP errors
  migrations/        Alembic schema migrations
  templates/         Jinja2 pages and HTML fragments
  static/            CSS, JavaScript, and Bootstrap
build/               Application Dockerfile
nginx/               Nginx image and proxy configuration
tests/               Application tests, PostgreSQL tests, and Myfin fixture
```

## Tests

With dependencies installed, run from the repository root:

```sh
python -m unittest discover -s tests -v
```

Tests use standard-library unittest and aiohttp test utilities, with no extra
test dependencies. Normal tests serve fixtures through a local HTTP server and
mock database persistence. They cover HTML and JSON routes, static assets,
Swagger, Myfin parsing, provider connection failures, and persistence errors
without contacting real providers or PostgreSQL.

The optional PostgreSQL integration test runs only when both variables below
are set. Use a **disposable database**: it applies migrations and inserts rows
that it does not remove.

```sh
export TEST_DATABASE_URI=postgresql+asyncpg://test:test@localhost:5432/currencycheck_test
export TEST_DATABASE_URI_MIGRATION=postgresql+psycopg2://test:test@localhost:5432/currencycheck_test
python -m unittest discover -s tests -v
```

This test verifies offline migration SQL, repeated `upgrade head`, and JSONB/text
persistence with PostgreSQL.
