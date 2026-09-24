#!/bin/sh
set -eu

target="${PROMETHEUS_BACKEND_TARGET:-host.docker.internal:8000}"
# Accept one host:port (or [IPv6]:port), without URL paths or YAML/sed metacharacters.
if [ "$(printf '%s\n' "$target" | wc -l)" -ne 1 ] ||
    ! printf '%s\n' "$target" | grep -Eq '^([a-zA-Z0-9_.-]+|\[[a-fA-F0-9:]+\]):[0-9]{1,5}$'; then
    echo "PROMETHEUS_BACKEND_TARGET must be a single host:port (no scheme or path)." >&2
    exit 1
fi

sed "s|__BACKEND_TARGET__|${target}|g" /etc/prometheus/prometheus.yml > /tmp/prometheus.yml
/bin/promtool check config /tmp/prometheus.yml
exec /bin/prometheus "$@"
