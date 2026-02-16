#!/bin/sh
# Custom entrypoint: write config files before SearXNG starts
# This bypasses the VOLUME /etc/searxng issue where COPY files are lost

mkdir -p /etc/searxng

# Write custom settings (disable limiter, enable JSON format)
cp /tmp/custom-settings.yml /etc/searxng/settings.yml
cp /tmp/custom-limiter.toml /etc/searxng/limiter.toml

echo "[custom-entrypoint] Settings and limiter config applied."

# Call the original SearXNG entrypoint
exec /usr/local/searxng/dockerfiles/docker-entrypoint.sh
