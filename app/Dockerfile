FROM python:3.15.2

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=ru_RU.UTF-8 LC_ALL=ru_RU.UTF-8

WORKDIR /project

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7777

CMD ["gunicorn", "app.server:current_app", "--bind", "0.0.0.0:7777", "--worker-class", "aiohttp.GunicornWebWorker", "--workers", "4"]
