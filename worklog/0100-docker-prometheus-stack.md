# Docker Prometheus Stack

- commit title: docker prometheus metrics stack
- changed file scope: Docker Compose observability services, Prometheus scrape config, Grafana datasources, backend observability docs
- reason: collect FastAPI `/metrics` from the local backend through the Docker observability stack and make Prometheus available from Grafana
- impact: local Prometheus runs on `localhost:9090`, scrapes `host.docker.internal:8000/metrics` by default, and Grafana has Prometheus plus Tempo datasources provisioned
