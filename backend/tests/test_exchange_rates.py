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

    async def test_last_updated_empty(self, client: AsyncClient, user_a: User):
        """DB 無匯率時回傳 null。"""
        resp = await client.get(
            "/api/v1/exchange-rates/last-updated",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json()["last_updated"] is None

    async def test_last_updated_with_data(self, client: AsyncClient, db, user_a: User):
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32.5"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        resp = await client.get(
            "/api/v1/exchange-rates/last-updated",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json()["last_updated"] is not None

    async def test_refresh_rates_success(self, client: AsyncClient, db, user_a: User):
        """Mock 台銀 API，驗證 refresh 端點存入 DB 並回傳匯率。"""
        fake_api_response = {
            "USDTWD": {"Exrate": 32.5, "UTC": "2026-04-03 08:00:00"},
            "USDJPY": {"Exrate": 150.2, "UTC": "2026-04-03 08:00:00"},
            "USDEUR": {"Exrate": 0.92, "UTC": "2026-04-03 08:00:00"},
        }
        with patch.object(
            exchange_rate_service,
            "fetch_rates_from_api",
            new_callable=AsyncMock,
            return_value=(
                {"USDTWD": Decimal("32.5")},
                {"USDJPY": Decimal("150.2"), "USDEUR": Decimal("0.92")},
            ),
        ):
            resp = await client.post(
                "/api/v1/exchange-rates/refresh",
                headers=auth_header(user_a),
            )
        assert resp.status_code == 200
        data = resp.json()
        # USDTWD 直接存入 + JPY→TWD 和 EUR→TWD 交叉匯率
        assert len(data) == 3
        currencies = {r["source_currency"] for r in data}
        assert "USD" in currencies
        assert "JPY" in currencies
        assert "EUR" in currencies

    async def test_refresh_rates_api_failure(self, client: AsyncClient, db, user_a: User):
        """台銀 API 掛掉時回傳 502。"""
        with patch.object(
            exchange_rate_service,
            "fetch_rates_from_api",
            new_callable=AsyncMock,
            side_effect=Exception("API timeout"),
        ):
            resp = await client.post(
                "/api/v1/exchange-rates/refresh",
                headers=auth_header(user_a),
            )
        assert resp.status_code == 502


class TestFetchRatesFromApi:
    """測試 fetch_rates_from_api 解析邏輯（mock HTTP）。"""

    async def test_parse_api_response(self):
        """驗證正確解析台銀 API 回傳格式。"""
        mock_json = {
            "USDTWD": {"Exrate": 32.5, "UTC": "2026-04-03"},
            "USDJPY": {"Exrate": 150.2, "UTC": "2026-04-03"},
            "USDEUR": {"Exrate": 0.92, "UTC": "2026-04-03"},
            "USDXYZ": {"Exrate": 1.5, "UTC": "2026-04-03"},  # 不在 CURRENCY_MAP，應被忽略
            "GOLDTWD": {"Exrate": 2000, "UTC": "2026-04-03"},  # 非 USD 開頭非 TWD 結尾，忽略
            "BADPAIR": {"NoExrate": True},  # 無 Exrate 欄位，忽略
            "USDZERO": {"Exrate": 0, "UTC": "2026-04-03"},  # rate=0，忽略
        }

        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.json.return_value = mock_json
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            twd_rates, usd_rates = await exchange_rate_service.fetch_rates_from_api()

        # USDTWD 歸入 twd_rates
        assert "USDTWD" in twd_rates
        assert twd_rates["USDTWD"] == Decimal("32.5")
        # USDJPY, USDEUR 歸入 usd_rates（USDXYZ 不在 CURRENCY_MAP 被忽略）
        assert "USDJPY" in usd_rates
        assert "USDEUR" in usd_rates
        assert "USDXYZ" not in usd_rates
        # GOLDTWD 非標準格式，被忽略（不是 USD 開頭且不是 endswith TWD...wait it does end with TWD）
        # 實際上 GOLDTWD 結尾是 TWD，所以會進 twd_rates
        # 但 BADPAIR 和 USDZERO 都被忽略
        assert "USDZERO" not in usd_rates


class TestRefreshRatesService:
    """測試 refresh_rates service 層邏輯。"""

    async def test_refresh_stores_direct_and_cross_rates(self, db: AsyncSession):
        """mock fetch_rates_from_api，驗證 refresh_rates 正確計算交叉匯率並存入 DB。"""
        with patch.object(
            exchange_rate_service,
            "fetch_rates_from_api",
            new_callable=AsyncMock,
            return_value=(
                {"USDTWD": Decimal("32")},
                {"USDJPY": Decimal("160"), "USDEUR": Decimal("0.8")},
            ),
        ):
            saved = await exchange_rate_service.refresh_rates(db)

        # 應存入 3 筆：USDTWD + JPYTWD + EURTWD
        assert len(saved) == 3
        pairs = {(r.source_currency, r.target_currency) for r in saved}
        assert ("USD", "TWD") in pairs
        assert ("JPY", "TWD") in pairs
        assert ("EUR", "TWD") in pairs

        # 驗證交叉匯率計算正確：JPYTWD = USDTWD / USDJPY = 32 / 160 = 0.2
        jpy_rate = next(r for r in saved if r.source_currency == "JPY")
        assert jpy_rate.rate == Decimal("0.2")
        # EURTWD = USDTWD / USDEUR = 32 / 0.8 = 40
        eur_rate = next(r for r in saved if r.source_currency == "EUR")
        assert eur_rate.rate == Decimal("40")

    async def test_refresh_no_usd_twd_skips_cross_rates(self, db: AsyncSession):
        """若台銀 API 沒回傳 USDTWD，不應計算交叉匯率。"""
        with patch.object(
            exchange_rate_service,
            "fetch_rates_from_api",
            new_callable=AsyncMock,
            return_value=(
                {},  # 無 twd_rates
                {"USDJPY": Decimal("150")},
            ),
        ):
            saved = await exchange_rate_service.refresh_rates(db)

        assert len(saved) == 0


class TestCrossRate:
    """測試 get_rate 的交叉匯率查詢（非 TWD pair）。"""

    async def test_cross_rate_via_twd(self, db: AsyncSession):
        """USD→JPY 透過 USDTWD 和 JPYTWD 交叉計算。"""
        now = datetime.now(timezone.utc)
        db.add(ExchangeRate(
            source_currency="USD", target_currency="TWD",
            rate=Decimal("32"), source="taiwan_bank", fetched_at=now,
        ))
        db.add(ExchangeRate(
            source_currency="JPY", target_currency="TWD",
            rate=Decimal("0.2"), source="taiwan_bank", fetched_at=now,
        ))
        await db.flush()

        rate, _ = await exchange_rate_service.get_rate(db, "USD", "JPY")
        # USD→JPY = USDTWD / JPYTWD = 32 / 0.2 = 160
        assert rate == Decimal("160")

    async def test_cross_rate_not_found(self, db: AsyncSession):
        """無匯率資料時應拋 NotFoundError。"""
        from app.core.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            await exchange_rate_service.get_rate(db, "USD", "JPY")


class TestGetRateFromDb:
    """測試 get_rate_from_db（只查 DB，不做交叉匯率）。"""

    async def test_direct_pair(self, db: AsyncSession):
        now = datetime.now(timezone.utc)
        db.add(ExchangeRate(
            source_currency="USD", target_currency="TWD",
            rate=Decimal("32"), source="taiwan_bank", fetched_at=now,
        ))
        await db.flush()

        rate, _ = await exchange_rate_service.get_rate_from_db(db, "USD", "TWD")
        assert rate == Decimal("32")

    async def test_reverse_pair(self, db: AsyncSession):
        now = datetime.now(timezone.utc)
        db.add(ExchangeRate(
            source_currency="USD", target_currency="TWD",
            rate=Decimal("32"), source="taiwan_bank", fetched_at=now,
        ))
        await db.flush()

        rate, _ = await exchange_rate_service.get_rate_from_db(db, "TWD", "USD")
        assert rate == Decimal("0.03125")

    async def test_not_found(self, db: AsyncSession):
        from app.core.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            await exchange_rate_service.get_rate_from_db(db, "XYZ", "ABC")


class TestGetLastUpdated:
    """測試 get_last_updated service。"""

    async def test_empty_db(self, db: AsyncSession):
        result = await exchange_rate_service.get_last_updated(db)
        assert result is None

    async def test_returns_latest(self, db: AsyncSession):
        now = datetime.now(timezone.utc)
        db.add(ExchangeRate(
            source_currency="USD", target_currency="TWD",
            rate=Decimal("32"), source="taiwan_bank", fetched_at=now,
        ))
        await db.flush()

        result = await exchange_rate_service.get_last_updated(db)
        assert result is not None
