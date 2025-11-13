FROM nginx:1.22.1

# удаляем старый html на всякий случай
RUN rm -rf /usr/share/nginx/html/*

# копируем все файлы из docs в html
COPY ../docs/* /usr/share/nginx/html/

# копируем конфиг
COPY nginx.conf /etc/nginx/templates/default.conf.template