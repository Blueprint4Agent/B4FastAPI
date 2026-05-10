# commit title
docker: add local OpenTelemetry tracing stack

# changed file scope
- docker/docker-compose.yml
- docker/.env.example
- docker/observability/otel-collector.yml
- docker/observability/tempo.yml
- docker/observability/grafana/provisioning/datasources/datasources.yml
- src/backend/README.md
- docs/ko/backend/README.md

# reason
- Local tracing needed runnable infrastructure for the backend's existing OTLP exporter.
- Grafana needs a provisioned Tempo datasource for trace exploration.
- Developers need documented local commands and environment values.
- User requested commit timestamp note: 2026-05-10 23:17 KST.

# impact
- Adds Tempo, OpenTelemetry Collector, and Grafana services to the Docker Compose stack.
- Routes backend traces through Collector to Tempo for Grafana Explore.
- Documents local tracing startup and backend env values in English and Korean docs.
- Uses a Tempo volume path that avoids local container permission failures.
