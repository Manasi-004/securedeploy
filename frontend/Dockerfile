FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html login.html signup.html cart.html nav.js app.js login.js signup.js cart.js style.css /usr/share/nginx/html/
USER nginx
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8081/ || exit 1
