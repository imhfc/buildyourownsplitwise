"""Tests for exchange rate service and API."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exchange_rate import ExchangeRate
from app.models.user import User
from app.services import exchange_rate_service
from tests.conftest import auth_header, create_test_user

pytestmark = pytest.mark.asyncio


class TestExchangeRateService:
    async def test_same_currency_returns_one(self, db: AsyncSession):
        rate, _ = await exchange_rate_service.get_rate(db, "TWD", "TWD")
        assert rate == Decimal("1")

    async def test_get_rate_from_db(self, db: AsyncSession):
        """Insert a rate directly and verify we can retrieve it."""
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32.50000000"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        rate, fetched_at = await exchange_rate_service.get_rate(db, "USD", "TWD")
        assert rate == Decimal("32.50000000")

    async def test_get_reverse_rate_from_db(self, db: AsyncSession):
        """If we have USD→TWD, we should be able to look up TWD→USD."""
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32.00000000"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        rate, _ = await exchange_rate_service.get_rate(db, "TWD", "USD")
        assert rate == Decimal("0.03125000")  # 1/32

    async def test_convert_amount(self, db: AsyncSession):
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32.00000000"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        converted, rate, _ = await exchange_rate_service.convert_amount(
            db, "USD", "TWD", Decimal("100")
        )
        assert converted == Decimal("3200.00")
        assert rate == Decimal("32.00000000")

    async def test_get_all_latest_rates(self, db: AsyncSession):
        now = datetime.now(timezone.utc)
        for currency, rate in [("USD", "32.5"), ("EUR", "35.2"), ("JPY", "0.22")]:
            er = ExchangeRate(
                source_currency=currency,
                target_currency="TWD",
                rate=Decimal(rate),
                source="taiwan_bank",
                fetched_at=now,
            )
            db.add(er)
        await db.flush()

        rates = await exchange_rate_service.get_all_latest_rates(db)
        assert len(rates) >= 3
        currencies = {r.source_currency for r in rates}
        assert "USD" in currencies
        assert "EUR" in currencies
        assert "JPY" in currencies


    async def test_get_available_currencies(self):
        currencies = await exchange_rate_service.get_available_currencies()
        assert len(currencies) > 0
        codes = [c["code"] for c in currencies]
        assert "TWD" in codes
        assert "USD" in codes
        assert "JPY" in codes
        # 確認按 code 排序
        assert codes == sorted(codes)
        # 確認每個幣別都有中英文名稱
        for c in currencies:
            assert c["code"]
            assert c["name_zh"]
            assert c["name_en"]


class TestExchangeRateAPI:
    async def test_list_rates_empty(self, client: AsyncClient, db, user_a: User):
        resp = await client.get(
            "/api/v1/exchange-rates",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_rates_with_data(self, client: AsyncClient, db, user_a: User):
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32.50000000"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        resp = await client.get(
            "/api/v1/exchange-rates",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["source_currency"] == "USD"

    async def test_get_specific_rate(self, client: AsyncClient, db, user_a: User):
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32.50000000"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        resp = await client.get(
            "/api/v1/exchange-rates/USD/TWD",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(data["rate"]) == Decimal("32.5")

    async def test_get_rate_not_found(self, client: AsyncClient, db, user_a: User):
        """When no rate exists and API fetch also fails, should return 404."""
        with patch.object(
            exchange_rate_service, "fetch_rates_from_api",
            new_callable=AsyncMock,
            side_effect=Exception("API down"),
        ):
            resp = await client.get(
                "/api/v1/exchange-rates/XYZ/ABC",
                headers=auth_header(user_a),
            )
            assert resp.status_code == 404

    async def test_convert_endpoint(self, client: AsyncClient, db, user_a: User):
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32.00000000"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        resp = await client.post(
            "/api/v1/exchange-rates/convert",
            headers=auth_header(user_a),
            json={
                "from_currency": "USD",
                "to_currency": "TWD",
                "amount": "100",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(data["converted_amount"]) == Decimal("3200")

    async def test_list_currencies(self, client: AsyncClient, db, user_a: User):
        resp = await client.get(
            "/api/v1/exchange-rates/currencies",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        codes = [c["code"] for c in data]
        assert "TWD" in codes
        assert "USD" in codes
        # 確認結構正確
        first = data[0]
        assert "code" in first
        assert "name_zh" in first
        assert "name_en" in first

    async def test_list_currencies_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/exchange-rates/currencies")
        assert resp.status_code == 403

    async def test_no_auth_returns_403(self, client: AsyncClient):
        resp = await client.get("/api/v1/exchange-rates")
        assert resp.status_code == 403
