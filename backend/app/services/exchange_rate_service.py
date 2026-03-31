"""Exchange rate service — fetches rates from 台銀 API, background refresh every 30 min."""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.exchange_rate import ExchangeRate

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = 30 * 60  # 30 minutes

# 台銀 API 可查到的幣別對照表（code → 中文名, 英文名）
CURRENCY_MAP: dict[str, tuple[str, str]] = {
    "TWD": ("新台幣", "New Taiwan Dollar"),
    "USD": ("美元", "US Dollar"),
    "EUR": ("歐元", "Euro"),
    "JPY": ("日圓", "Japanese Yen"),
    "GBP": ("英鎊", "British Pound"),
    "AUD": ("澳幣", "Australian Dollar"),
    "CAD": ("加拿大幣", "Canadian Dollar"),
    "CHF": ("瑞士法郎", "Swiss Franc"),
    "CNY": ("人民幣", "Chinese Yuan"),
    "HKD": ("港幣", "Hong Kong Dollar"),
    "KRW": ("韓元", "South Korean Won"),
    "SGD": ("新加坡幣", "Singapore Dollar"),
    "THB": ("泰銖", "Thai Baht"),
    "NZD": ("紐西蘭幣", "New Zealand Dollar"),
    "SEK": ("瑞典克朗", "Swedish Krona"),
    "ZAR": ("南非幣", "South African Rand"),
    "MYR": ("馬來幣", "Malaysian Ringgit"),
    "PHP": ("菲律賓披索", "Philippine Peso"),
    "IDR": ("印尼盾", "Indonesian Rupiah"),
    "VND": ("越南盾", "Vietnamese Dong"),
    "INR": ("印度盧比", "Indian Rupee"),
}


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
    """Fetch latest rates from API and store in DB."""
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
    return saved


async def _get_single_rate(
    db: AsyncSession, currency: str, target: str = "TWD"
) -> tuple[Decimal, datetime] | None:
    """Get rate for a single currency pair from DB (direct + reverse). Returns None if not found."""
    result = await db.execute(
        select(ExchangeRate)
        .where(ExchangeRate.source_currency == currency, ExchangeRate.target_currency == target)
        .order_by(ExchangeRate.fetched_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if record:
        return record.rate, record.fetched_at
    # reverse
    result = await db.execute(
        select(ExchangeRate)
        .where(ExchangeRate.source_currency == target, ExchangeRate.target_currency == currency)
        .order_by(ExchangeRate.fetched_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if record:
        return round(Decimal("1") / record.rate, 8), record.fetched_at
    return None


async def get_rate(
    db: AsyncSession, source_currency: str, target_currency: str
) -> tuple[Decimal, datetime]:
    """
    Get exchange rate between two currencies from DB only.
    Returns (rate, fetched_at).

    Rates are pre-populated by the background refresh task.
    Lookup order: direct pair → reverse pair → cross-rate via TWD.
    """
    source_currency = source_currency.upper()
    target_currency = target_currency.upper()

    if source_currency == target_currency:
        return Decimal("1"), datetime.now(timezone.utc)

    # Try direct pair
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

    # Try reverse pair
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

    # Cross-rate via TWD: e.g. USD→THB = (USDTWD) / (THBTWD)
    if source_currency != "TWD" and target_currency != "TWD":
        src_to_twd = await _get_single_rate(db, source_currency, "TWD")
        tgt_to_twd = await _get_single_rate(db, target_currency, "TWD")
        if src_to_twd and tgt_to_twd:
            rate = round(src_to_twd[0] / tgt_to_twd[0], 8)
            return rate, max(src_to_twd[1], tgt_to_twd[1])

    raise NotFoundError(f"Exchange rate not found for {source_currency} → {target_currency}")


async def get_rate_from_db(
    db: AsyncSession, source_currency: str, target_currency: str
) -> tuple[Decimal, datetime]:
    """Get the latest rate from DB only (tries reverse pair too)."""
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

    # Try reverse pair
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

    raise NotFoundError(f"Exchange rate not found for {source_currency} → {target_currency}")


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


async def get_available_currencies() -> list[dict[str, str]]:
    """Return all currencies that have exchange rate data available."""
    return [
        {"code": code, "name_zh": name_zh, "name_en": name_en}
        for code, (name_zh, name_en) in sorted(CURRENCY_MAP.items())
    ]


async def get_all_latest_rates(db: AsyncSession) -> list[ExchangeRate]:
    """Get all latest exchange rates (one per currency pair)."""
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


async def get_last_updated(db: AsyncSession) -> datetime | None:
    """Get the most recent fetched_at timestamp across all rates."""
    result = await db.execute(
        select(func.max(ExchangeRate.fetched_at))
    )
    return result.scalar_one_or_none()


async def background_refresh_loop() -> None:
    """Background task: refresh exchange rates every 30 minutes."""
    from app.core.database import async_session

    while True:
        try:
            async with async_session() as db:
                await refresh_rates(db)
                await db.commit()
            logger.info("Exchange rates refreshed successfully")
        except Exception:
            logger.exception("Failed to refresh exchange rates")
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)
