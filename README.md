# CurrencyCheckAiohttp

This application get info about currency courses from different sources.

---------------------------------
# docker_settings.env
If you want to run project in production, you should to create docker_settings.env, <br>
insert file into the root of project and set next settings

```dotenv
APP_HOST=0.0.0.0
APP_PORT=?
DATABASE_URI=postgresql+asyncpg://db_user:db_user_pass@db_hostname:db_port/currency_exchange_db
DATABASE_URI_MIGRATION=postgresql+psycopg2://db_user:db_user_pass@db:db_port/currency_exchange_db
POSTGRES_DB=currency_exchange_db
POSTGRES_USER=db_user
POSTGRES_PASSWORD=db_user_pass
```

Run `./deploy.sh` to build and start the production services. Existing build
layers are reused, and changed services are recreated without removing images.
The application is available at `http://localhost:99`.

For local development, run `./db_run.sh` to start the development database in
the foreground. Configure
`local_settings.env` and apply migrations before running `./start.sh`, which
starts Gunicorn at `http://localhost:8000` using the active Python environment.

Run all scripts from the repository root.
