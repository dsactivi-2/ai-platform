FROM searxng/searxng:latest

# Copy custom settings that disable bot detection limiter
COPY settings.yml /etc/searxng/settings.yml
COPY limiter.toml /etc/searxng/limiter.toml

EXPOSE 8080
