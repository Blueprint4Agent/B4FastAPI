# Grafana FastAPI Dashboard

- commit title: docker grafana fastapi dashboard
- changed file scope: Grafana dashboard provisioning, Grafana datasource UIDs, backend observability docs
- reason: make the FastAPI metrics dashboard available automatically when the local observability stack starts
- impact: Grafana provisions `B4FastAPI / FastAPI Overview` with backend target status, request rate, 5xx ratio, p95 latency, and endpoint-level metric panels
