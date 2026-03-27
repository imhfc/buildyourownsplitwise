"""Exchange rate service — fetches rates from 台銀 API and caches in Redis."""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.redis import get_redis
from app.models.exchange_rate import ExchangeRate

logger = logging.getLogger(__name__)

CACHE_KEY = "exchange_rates:latest"


async def fetch_rates_from_api() -> dict[str, Decimal]:
    """
    Fetch exchange rates from tw.rter.info (台銀匯率 API).
    Returns a dict mapping currency pair to rate, e.g. {"USDTWD": Decimal("32.5"), ...}

    The API returns JSON like:
    {
        "USDTWD": {"Exrate": 32.5, "UTC": "2024-01-01 00:00:00"},
        "EURTWD": {"Exrate": 35.2, "UTC": "2024-01-01 00:00:00"},
        ...
    }
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(settings.EXCHANGE_RATE_API_URL)
        resp.raise_for_status()
        data = resp.json()

    rates = {}
    for pair, info in data.items():
        if "Exrate" in info and pair.endswith("TWD"):
            rate_value = info["Exrate"]
            if rate_value and float(rate_value) > 0:
                rates[pair] = Decimal(str(rate_value))
    return rates


async def refresh_rates(db: AsyncSession) -> list[ExchangeRate]:
    """Fetch latest rates from API, store in DB and Redis cache."""
    raw_rates = await fetch_rates_from_api()
    now = datetime.now(timezone.utc)
    saved = []

    for pair, rate in raw_rates.items():
        source_currency = pair[:3]  # e.g. "USD" from "USDTWD"
        target_currency = pair[3:]  # e.g. "TWD"

        exchange_rate = ExchangeRate(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=rate,
            source="taiwan_bank",
            fetched_at=now,
        )
        db.add(exchange_rate)
        saved.append(exchange_rate)

    await db.flush()

    # Cache in Redis
    try:
        redis = await get_redis()
        cache_data = {
            pair: str(rate) for pair, rate in raw_rates.items()
        }
        cache_data["_fetched_at"] = now.isoformat()
        await redis.set(CACHE_KEY, json.dumps(cache_data), ex=settings.EXCHANGE_RATE_CACHE_TTL)
    except Exception:
        logger.warning("Failed to cache exchange rates in Redis, continuing without cache")

    return saved


async def get_rate(
    db: AsyncSession, source_currency: str, target_currency: str
) -> tuple[Decimal, datetime]:
    """
    Get exchange rate between two currencies.
    Returns (rate, fetched_at).

    Lookup order: Redis cache → DB → fetch from API.
    """
    source_currency = source_currency.upper()
    target_currency = target_currency.upper()

    if source_currency == target_currency:
        return Decimal("1"), datetime.now(timezone.utc)

    # Try Redis cache first
    pair_key = f"{source_currency}{target_currency}"
    try:
        redis = await get_redis()
        cached = await redis.get(CACHE_KEY)
        if cached:
            data = json.loads(cached)
            if pair_key in data:
                return Decimal(data[pair_key]), datetime.fromisoformat(data["_fetched_at"])
            # Try reverse pair
            reverse_key = f"{target_currency}{source_currency}"
            if reverse_key in data:
                rate = Decimal("1") / Decimal(data[reverse_key])
                return round(rate, 8), datetime.fromisoformat(data["_fetched_at"])
    except Exception:
        logger.warning("Redis cache miss or error, falling back to DB")

    # Try DB — get latest rate
    result = await db.execute(
        select(ExchangeRate)
        .where(
            ExchangeRate.source_currency == source_currency,
            ExchangeRate.target_currency == target_currency,
        )
        .order_by(ExchangeRate.fetched_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if record:
        return record.rate, record.fetched_at

    # Try reverse
    result = await db.execute(
        select(ExchangeRate)
        .where(
            ExchangeRate.source_currency == target_currency,
            ExchangeRate.target_currency == source_currency,
        )
        .order_by(ExchangeRate.fetched_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if record:
        rate = Decimal("1") / record.rate
        return round(rate, 8), record.fetched_at

    # Fetch from API as last resort
    try:
        await refresh_rates(db)
        return await get_rate_from_db(db, source_currency, target_currency)
    except Exception as e:
        raise NotFoundError(f"Exchange rate not found for {source_currency} → {target_currency}")


async def get_rate_from_db(
    db: AsyncSession, source_currency: str, target_currency: str
) -> tuple[Decimal, datetime]:
    """Get the latest rate from DB only."""
    result = await db.execute(
        select(ExchangeRate)
        .where(
            ExchangeRate.source_currency == source_currency,
            ExchangeRate.target_currency == target_currency,
        )
        .order_by(ExchangeRate.fetched_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise NotFoundError(f"Exchange rate not found for {source_currency} → {target_currency}")
    return record.rate, record.fetched_at


async def convert_amount(
    db: AsyncSession,
    from_currency: str,
    to_currency: str,
    amount: Decimal,
) -> tuple[Decimal, Decimal, datetime]:
    """Convert amount between currencies. Returns (converted_amount, rate, fetched_at)."""
    rate, fetched_at = await get_rate(db, from_currency, to_currency)
    converted = round(amount * rate, 2)
    return converted, rate, fetched_at


async def get_all_latest_rates(db: AsyncSession) -> list[ExchangeRate]:
    """Get all latest exchange rates (one per currency pair)."""
    # Use a subquery to get latest fetched_at per pair
    from sqlalchemy import func

    subq = (
        select(
            ExchangeRate.source_currency,
            ExchangeRate.target_currency,
            func.max(ExchangeRate.fetched_at).label("max_fetched_at"),
        )
        .group_by(ExchangeRate.source_currency, ExchangeRate.target_currency)
        .subquery()
    )

    result = await db.execute(
        select(ExchangeRate)
        .join(
            subq,
            (ExchangeRate.source_currency == subq.c.source_currency)
            & (ExchangeRate.target_currency == subq.c.target_currency)
            & (ExchangeRate.fetched_at == subq.c.max_fetched_at),
        )
        .order_by(ExchangeRate.source_currency)
    )
    return list(result.scalars().all())
