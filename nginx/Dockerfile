FROM nginx:1.22.1

# очищаем стандартный html
RUN rm -rf /usr/share/nginx/html/*

# копируем документацию
COPY docs/* /usr/share/nginx/html/

# копируем конфиг nginx
COPY nginx.conf /etc/nginx/templates/default.conf.template