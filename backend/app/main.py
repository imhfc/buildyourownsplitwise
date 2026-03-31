import asyncio
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import activities, auth, exchange_rates, expenses, friends, groups, settlements
from app.core.config import settings
from app.services.exchange_rate_service import background_refresh_loop

logger = logging.getLogger(__name__)


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)


@app.on_event("startup")
async def startup_exchange_rate_refresh():
    asyncio.create_task(background_refresh_loop())

_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(groups.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")
app.include_router(settlements.router, prefix="/api/v1")
app.include_router(exchange_rates.router, prefix="/api/v1")
app.include_router(friends.router, prefix="/api/v1")
app.include_router(activities.router, prefix="/api/v1")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
