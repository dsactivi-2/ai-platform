FROM searxng/searxng:latest

# Copy custom settings to a temp location (VOLUME /etc/searxng overrides COPY at runtime)
COPY settings.yml /tmp/custom-settings.yml
COPY limiter.toml /tmp/custom-limiter.toml

# Custom entrypoint that writes config before the default entrypoint runs
COPY entrypoint.sh /usr/local/bin/custom-entrypoint.sh
RUN chmod +x /usr/local/bin/custom-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/custom-entrypoint.sh"]
