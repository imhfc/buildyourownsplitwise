from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.exchange_rate import CurrencyInfo, ExchangeRateConvert, ExchangeRateConvertResponse, ExchangeRateLastUpdated, ExchangeRateResponse
from app.services import exchange_rate_service

router = APIRouter(prefix="/exchange-rates", tags=["exchange-rates"])


@router.get("/currencies", response_model=list[CurrencyInfo])
async def list_currencies(
    current_user: User = Depends(get_current_user),
):
    """Get all available currencies with names."""
    return await exchange_rate_service.get_available_currencies()


@router.get("/last-updated", response_model=ExchangeRateLastUpdated)
async def last_updated(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the timestamp of the most recent exchange rate update."""
    ts = await exchange_rate_service.get_last_updated(db)
    return ExchangeRateLastUpdated(last_updated=ts)


@router.get("", response_model=list[ExchangeRateResponse])
async def list_rates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all latest exchange rates."""
    return await exchange_rate_service.get_all_latest_rates(db)


@router.post("/refresh", response_model=list[ExchangeRateResponse])
async def refresh_rates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a rate refresh from 台銀 API."""
    try:
        rates = await exchange_rate_service.refresh_rates(db)
        return rates
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch rates: {str(e)}")


@router.get("/{source}/{target}", response_model=ExchangeRateResponse)
async def get_rate(
    source: str,
    target: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get exchange rate for a specific currency pair."""
    try:
        rate, fetched_at = await exchange_rate_service.get_rate(db, source, target)
        return ExchangeRateResponse(
            source_currency=source.upper(),
            target_currency=target.upper(),
            rate=rate,
            source="taiwan_bank",
            fetched_at=fetched_at,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/convert", response_model=ExchangeRateConvertResponse)
async def convert(
    data: ExchangeRateConvert,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert an amount between currencies."""
    try:
        converted, rate, fetched_at = await exchange_rate_service.convert_amount(
            db, data.from_currency, data.to_currency, data.amount
        )
        return ExchangeRateConvertResponse(
            from_currency=data.from_currency.upper(),
            to_currency=data.to_currency.upper(),
            original_amount=data.amount,
            converted_amount=converted,
            rate=rate,
            fetched_at=fetched_at,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
