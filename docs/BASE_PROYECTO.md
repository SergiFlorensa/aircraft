# Aircraft Fleet Monitor — Base del Proyecto

## Objetivo
Sistema event-driven (100% open-source) para:
- Recibir eventos de telemetría (posición/altitud/velocidad)
- Procesarlos con workers
- Calcular health score por aeronave
- Generar alertas
- Guardar histórico en Postgres
- Exponer API REST (FastAPI)
- Métricas/observabilidad (Prometheus/Grafana) en fases posteriores

## Reglas
- Solo herramientas **libres/gratuitas**, sin suscripciones.
- Todo reproducible con Docker Compose.
- Código modular: api / servicios / dominio / db.
- Cada feature “terminado” = tests + docs + CI verde.

## Stack (MVP)
- Python 3.11+
- FastAPI
- Redis Streams (bus)
- PostgreSQL (DB)
- pytest, ruff, black
- Docker + docker-compose

## MVP (definición de “acabado”)
- Endpoint `GET /health`
- `docker compose up` levanta: redis + postgres + backend
- Test `test_health` pasando
- README con comandos

## Endpoints iniciales
- GET /health -> {"status":"ok"}
