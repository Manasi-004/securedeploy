FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html login.html signup.html cart.html nav.js app.js login.js signup.js cart.js style.css /usr/share/nginx/html/
EXPOSE 8081