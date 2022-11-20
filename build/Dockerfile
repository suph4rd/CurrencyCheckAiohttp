FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1


RUN apt-get update
RUN apt-get install curl

COPY . /project

WORKDIR /project

RUN pip3 install -r requirements.txt

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8

EXPOSE 7777

CMD gunicorn app.server:current_app --bind 0.0.0.0:7777 --worker-class aiohttp.GunicornWebWorker --workers 4
