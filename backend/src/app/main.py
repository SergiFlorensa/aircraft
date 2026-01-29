from fastapi import FastAPI
from app.api.routes_events import router as events_router
from app.api.routes_health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Aircraft Fleet Monitor API", version="0.1.0")
    app.include_router(events_router)
    app.include_router(health_router)
    return app


app = create_app()
