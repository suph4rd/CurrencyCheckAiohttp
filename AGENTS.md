# Repository Guidelines

## Language Guidelines

Communicate with the user in Russian, including replies, explanations, and progress reports. Maintain the project in English: use English for documentation, code comments, identifiers, commit messages, and pull request descriptions. Follow these defaults unless the user explicitly requests otherwise.

## Project Structure & Module Organization

This Python 3.10 application collects currency exchange rates from Belarusbank and Myfin, serves HTML and JSON through aiohttp, and stores responses in PostgreSQL.

- `app/server.py` initializes the application; `routes.py` maps URLs and `views.py` implements HTTP handlers.
- `app/service.py` fetches, parses, and persists provider responses.
- `app/database.py` and `models.py` define asynchronous SQLAlchemy access and database models.
- `app/migrations/` contains Alembic migrations; `app/alembic.ini` configures them.
- `app/templates/` contains Jinja2 templates; `app/static/` contains CSS, JavaScript, and bundled Bootstrap assets.
- `build/`, `nginx/`, and the Compose files define container deployment. No test directory currently exists.

## Build, Test, and Development Commands

Run commands from the repository root unless stated otherwise.

- `python3.10 -m venv .venv` and `source .venv/bin/activate`: create and activate a local environment.
- `pip install -r requirements.txt`: install pinned dependencies.
- `docker compose up --build`: build and run the development application and PostgreSQL; access the application at `http://localhost:7777`.
- `cd app && alembic upgrade head`: apply migrations with database environment variables configured.
- `bash start.sh`: run Gunicorn locally on port 8000 after configuring the database and applying migrations.
- `docker compose -f docker-compose-prod.yml up -d --build`: start production services using `docker_settings.env`.

## Coding Style & Naming Conventions

Use four-space indentation, snake_case for functions and variables, PascalCase for classes, and UPPER_SNAKE_CASE for constants. Follow existing type annotations and asynchronous request/database patterns. Keep provider parsing in service classes and HTTP behavior in views. No formatter or linter is currently configured.

## Testing Guidelines

No automated test framework or coverage threshold is configured. Verify changes against the relevant HTML and `/api/` routes, including provider failures and database persistence. For new automated tests, use a `tests/` directory with `test_*.py` filenames; document dependencies and the execution command. Mock upstream responses for repeatable parser tests.

## Commit & Pull Request Guidelines

History uses short imperative subjects with `feat:` and `fix:` prefixes. Follow this pattern, for example `fix: handle missing Myfin currency rows`. Describe behavior changes, link relevant issues, and record validation steps in pull requests. Include screenshots for template or styling changes and migration notes for schema changes.

## Security & Configuration

Keep credentials in ignored `local_settings.env` or `docker_settings.env` files. Configure `DATABASE_URI` with asyncpg and `DATABASE_URI_MIGRATION` with psycopg2. Never commit production credentials; development Compose credentials are local examples.
