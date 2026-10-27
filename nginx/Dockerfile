FROM nginx:1.19.0-alpine
RUN rm /etc/nginx/conf.d/*
COPY nginx/conf/nginx.conf /etc/nginx/conf.d/
COPY app/static/ /project/app/static/
