FROM nginx:1.30.6-alpine
RUN rm /etc/nginx/conf.d/*
COPY nginx/conf/nginx.conf /etc/nginx/conf.d/
COPY app/static/ /project/app/static/
