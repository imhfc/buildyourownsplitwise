"""Exchange rate service — dual source: 台銀 (TWD pairs, 30 min) + OXR (all others, 1 hr)."""

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

TWB_REFRESH_INTERVAL = 30 * 60   # 台銀: 30 分鐘
OXR_REFRESH_INTERVAL = 60 * 60   # OXR: 1 小時

# 台銀 API 直接提供的幣別（TWD 相關匯率最準）
TWB_CURRENCIES: set[str] = {
    "TWD", "USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "CNY",
    "HKD", "KRW", "SGD", "THB", "NZD", "SEK", "ZAR", "MYR", "PHP",
    "IDR", "VND", "INR",
}

# 完整幣別對照表（code → 中文名, 英文名）
# 台銀有的 + OXR 補齊的常用幣別
CURRENCY_MAP: dict[str, tuple[str, str]] = {
    # --- 台銀直接提供 ---
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
    # --- OXR 補齊：歐洲 ---
    "DKK": ("丹麥克朗", "Danish Krone"),
    "NOK": ("挪威克朗", "Norwegian Krone"),
    "PLN": ("波蘭茲羅提", "Polish Zloty"),
    "CZK": ("捷克克朗", "Czech Koruna"),
    "HUF": ("匈牙利福林", "Hungarian Forint"),
    "RON": ("羅馬尼亞列伊", "Romanian Leu"),
    "BGN": ("保加利亞列弗", "Bulgarian Lev"),
    "HRK": ("克羅埃西亞庫納", "Croatian Kuna"),
    "ISK": ("冰島克朗", "Icelandic Krona"),
    "RUB": ("俄羅斯盧布", "Russian Ruble"),
    "UAH": ("烏克蘭格里夫納", "Ukrainian Hryvnia"),
    "TRY": ("土耳其里拉", "Turkish Lira"),
    # --- OXR 補齊：中東/非洲 ---
    "AED": ("阿聯酋迪拉姆", "UAE Dirham"),
    "SAR": ("沙烏地里亞爾", "Saudi Riyal"),
    "QAR": ("卡達里亞爾", "Qatari Riyal"),
    "KWD": ("科威特第納爾", "Kuwaiti Dinar"),
    "BHD": ("巴林第納爾", "Bahraini Dinar"),
    "OMR": ("阿曼里亞爾", "Omani Rial"),
    "ILS": ("以色列謝克爾", "Israeli Shekel"),
    "EGP": ("埃及鎊", "Egyptian Pound"),
    "NGN": ("奈及利亞奈拉", "Nigerian Naira"),
    "KES": ("肯亞先令", "Kenyan Shilling"),
    # --- OXR 補齊：亞太 ---
    "PKR": ("巴基斯坦盧比", "Pakistani Rupee"),
    "BDT": ("孟加拉塔卡", "Bangladeshi Taka"),
    "LKR": ("斯里蘭卡盧比", "Sri Lankan Rupee"),
    "MMK": ("緬甸元", "Myanmar Kyat"),
    "KHR": ("柬埔寨瑞爾", "Cambodian Riel"),
    "LAK": ("寮國基普", "Lao Kip"),
    "MNT": ("蒙古圖格里克", "Mongolian Tugrik"),
    "NPR": ("尼泊爾盧比", "Nepalese Rupee"),
    "FJD": ("斐濟元", "Fijian Dollar"),
    "MOP": ("澳門幣", "Macanese Pataca"),
    # --- OXR 補齊：美洲 ---
    "MXN": ("墨西哥披索", "Mexican Peso"),
    "BRL": ("巴西雷亞爾", "Brazilian Real"),
    "ARS": ("阿根廷披索", "Argentine Peso"),
    "CLP": ("智利披索", "Chilean Peso"),
    "COP": ("哥倫比亞披索", "Colombian Peso"),
    "PEN": ("秘魯索爾", "Peruvian Sol"),
    "UYU": ("烏拉圭披索", "Uruguayan Peso"),
    "DOP": ("多明尼加披索", "Dominican Peso"),
    "CRC": ("哥斯大黎加科朗", "Costa Rican Colon"),
    "JMD": ("牙買加元", "Jamaican Dollar"),
    # --- OXR 補齊：其他 ---
    "XAF": ("中非法郎", "Central African CFA Franc"),
    "XOF": ("西非法郎", "West African CFA Franc"),
}


async def fetch_twb_rates() -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    """
    Fetch exchange rates from tw.rter.info (台銀匯率 API).

    Returns:
        (twd_rates, usd_rates):
        - twd_rates: {"USDTWD": Decimal("31.95")}
        - usd_rates: {"USDTHB": Decimal("32.7"), ...}
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(settings.EXCHANGE_RATE_API_URL)
        resp.raise_for_status()
        data = resp.json()

    twd_rates: dict[str, Decimal] = {}
    usd_rates: dict[str, Decimal] = {}

    for pair, info in data.items():
        if "Exrate" not in info:
            continue
        rate_value = info["Exrate"]
        if not rate_value or float(rate_value) <= 0:
            continue

        rate_decimal = Decimal(str(rate_value))

        if pair.endswith("TWD"):
            twd_rates[pair] = rate_decimal
        elif pair.startswith("USD") and len(pair) == 6:
            target_cur = pair[3:]
            if target_cur in CURRENCY_MAP:
                usd_rates[pair] = rate_decimal

    return twd_rates, usd_rates


async def fetch_oxr_rates() -> dict[str, Decimal]:
    """
    Fetch exchange rates from Open Exchange Rates (USD base).

    Returns:
        {"EUR": Decimal("0.92"), "JPY": Decimal("149.5"), ...}
    """
    if not settings.OXR_APP_ID:
        logger.warning("OXR_APP_ID not configured, skipping OXR fetch")
        return {}

    url = f"https://openexchangerates.org/api/latest.json?app_id={settings.OXR_APP_ID}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    rates: dict[str, Decimal] = {}
    for code, value in data.get("rates", {}).items():
        if code in CURRENCY_MAP and code != "USD":
            rates[code] = Decimal(str(value))

    return rates


async def refresh_twb_rates(db: AsyncSession) -> list[ExchangeRate]:
    """Fetch 台銀 rates and store in DB. Source = 'taiwan_bank'."""
    twd_rates, usd_rates = await fetch_twb_rates()
    now = datetime.now(timezone.utc)
    saved = []

    for pair, rate in twd_rates.items():
        source_currency = pair[:3]
        target_currency = pair[3:]
        exchange_rate = ExchangeRate(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=rate,
            source="taiwan_bank",
            fetched_at=now,
        )
        db.add(exchange_rate)
        saved.append(exchange_rate)

    usd_twd_rate = twd_rates.get("USDTWD")
    if usd_twd_rate:
        for pair, usd_xxx_rate in usd_rates.items():
            xxx = pair[3:]
            xxx_twd_rate = round(usd_twd_rate / usd_xxx_rate, 8)
            exchange_rate = ExchangeRate(
                source_currency=xxx,
                target_currency="TWD",
                rate=xxx_twd_rate,
                source="taiwan_bank",
                fetched_at=now,
            )
            db.add(exchange_rate)
            saved.append(exchange_rate)

    await db.flush()
    return saved


async def refresh_oxr_rates(db: AsyncSession) -> list[ExchangeRate]:
    """Fetch OXR rates (USD base) and store in DB. Source = 'oxr'."""
    usd_rates = await fetch_oxr_rates()
    if not usd_rates:
        return []

    now = datetime.now(timezone.utc)
    saved = []

    # 存入 USD→XXX 匯率（跳過台銀已覆蓋的 TWD 相關幣對）
    for code, rate in usd_rates.items():
        exchange_rate = ExchangeRate(
            source_currency="USD",
            target_currency=code,
            rate=rate,
            source="oxr",
            fetched_at=now,
        )
        db.add(exchange_rate)
        saved.append(exchange_rate)

    await db.flush()
    return saved


async def refresh_rates(db: AsyncSession) -> list[ExchangeRate]:
    """Refresh from both sources (for manual trigger)."""
    saved = await refresh_twb_rates(db)
    saved += await refresh_oxr_rates(db)
    return saved



async def _get_single_rate_any_pivot(
    db: AsyncSession, currency: str, pivot: str
) -> tuple[Decimal, datetime] | None:
    """Get rate for currency→pivot from DB (direct + reverse). Returns None if not found."""
    result = await db.execute(
        select(ExchangeRate)
        .where(ExchangeRate.source_currency == currency, ExchangeRate.target_currency == pivot)
        .order_by(ExchangeRate.fetched_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if record:
        return record.rate, record.fetched_at
    # reverse
    result = await db.execute(
        select(ExchangeRate)
        .where(ExchangeRate.source_currency == pivot, ExchangeRate.target_currency == currency)
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

    Lookup order:
    1. Direct pair (any source)
    2. Reverse pair
    3. Cross-rate via TWD (台銀 pairs)
    4. Cross-rate via USD (OXR pairs)
    """
    source_currency = source_currency.upper()
    target_currency = target_currency.upper()

    if source_currency == target_currency:
        return Decimal("1"), datetime.now(timezone.utc)

    # 1. Try direct pair
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

    # 2. Try reverse pair
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

    # 3. Cross-rate via TWD: e.g. EUR→THB = (EURTWD) / (THBTWD)
    if source_currency != "TWD" and target_currency != "TWD":
        src_to_twd = await _get_single_rate_any_pivot(db, source_currency, "TWD")
        tgt_to_twd = await _get_single_rate_any_pivot(db, target_currency, "TWD")
        if src_to_twd and tgt_to_twd:
            rate = round(src_to_twd[0] / tgt_to_twd[0], 8)
            return rate, max(src_to_twd[1], tgt_to_twd[1])

    # 4. Cross-rate via USD: e.g. MXN→TRY = (USD→MXN)^-1 * (USD→TRY)
    if source_currency != "USD" and target_currency != "USD":
        src_to_usd = await _get_single_rate_any_pivot(db, source_currency, "USD")
        tgt_to_usd = await _get_single_rate_any_pivot(db, target_currency, "USD")
        if src_to_usd and tgt_to_usd:
            rate = round(src_to_usd[0] / tgt_to_usd[0], 8)
            return rate, max(src_to_usd[1], tgt_to_usd[1])

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


async def _twb_refresh_loop() -> None:
    """Background task: refresh 台銀 rates every 30 minutes."""
    from app.core.database import async_session

    while True:
        try:
            async with async_session() as db:
                saved = await refresh_twb_rates(db)
                await db.commit()
            logger.info("Taiwan Bank rates refreshed: %d pairs", len(saved))
        except Exception:
            logger.exception("Failed to refresh Taiwan Bank rates")
        await asyncio.sleep(TWB_REFRESH_INTERVAL)


async def _oxr_refresh_loop() -> None:
    """Background task: refresh OXR rates every 1 hour."""
    from app.core.database import async_session

    if not settings.OXR_APP_ID:
        logger.warning("OXR_APP_ID not configured, OXR refresh loop disabled")
        return

    while True:
        try:
            async with async_session() as db:
                saved = await refresh_oxr_rates(db)
                await db.commit()
            logger.info("OXR rates refreshed: %d pairs", len(saved))
        except Exception:
            logger.exception("Failed to refresh OXR rates")
        await asyncio.sleep(OXR_REFRESH_INTERVAL)


async def background_refresh_loop() -> None:
    """Launch both refresh loops concurrently."""
    await asyncio.gather(
        _twb_refresh_loop(),
        _oxr_refresh_loop(),
    )
