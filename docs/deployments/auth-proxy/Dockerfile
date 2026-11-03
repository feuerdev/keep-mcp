FROM caddy:2-alpine

# Copy custom Caddy reverse proxy configuration
COPY Caddyfile /etc/caddy/Caddyfile

# Default container port
EXPOSE 8080

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
