FROM nginx:1.14

COPY ./docker/nginx/000-frontend.conf /etc/nginx/conf.d
COPY ./docker/nginx/001-api.conf /etc/nginx/conf.d
COPY ./docker/nginx/002-admin.conf /etc/nginx/conf.d
COPY ./docker/nginx/003-kibana.conf /etc/nginx/conf.d
COPY ./docker/nginx/004-apm.conf /etc/nginx/conf.d
