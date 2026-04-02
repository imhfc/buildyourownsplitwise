import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import ExpenseCategory
from tests.conftest import auth_header


pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def default_categories(db: AsyncSession):
    """建立預設分類供測試使用。"""
    categories = [
        ExpenseCategory(name="Food", icon="utensils", color="#FF6B6B", is_default=True),
        ExpenseCategory(name="Transport", icon="car", color="#4ECDC4", is_default=True),
        ExpenseCategory(name="Entertainment", icon="film", color="#FFE66D", is_default=True),
    ]
    for cat in categories:
        db.add(cat)
    await db.flush()
    return categories


class TestListCategories:
    async def test_list_default_categories(
        self, client: AsyncClient, user_a, default_categories
    ):
        """應列出所有預設分類。"""
        resp = await client.get("/api/v1/categories", headers=auth_header(user_a))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert all(item["is_default"] for item in data)
        names = [item["name"] for item in data]
        assert "Food" in names
        assert "Transport" in names
        assert "Entertainment" in names

    async def test_list_categories_with_group_id(
        self, client: AsyncClient, db: AsyncSession, user_a, group_with_members, default_categories
    ):
        """指定 group_id 時應包含該群組的自訂分類。"""
        # 建立自訂分類
        custom = ExpenseCategory(
            name="custom_cat",
            icon="star",
            color="#9B59B6",
            group_id=group_with_members.id,
            created_by=user_a.id,
            is_default=False,
        )
        db.add(custom)
        await db.flush()

        resp = await client.get(
            "/api/v1/categories",
            headers=auth_header(user_a),
            params={"group_id": str(group_with_members.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        # 應包含所有預設分類 + 自訂分類
        assert len(data) == 4
        names = [c["name"] for c in data]
        assert "custom_cat" in names
        assert "Food" in names

    async def test_list_categories_group_id_excludes_other_groups(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, default_categories
    ):
        """不同群組的自訂分類不應出現。"""
        # 建立兩個群組
        from app.models.group import Group, GroupMember

        group1 = Group(name="Group 1", created_by=user_a.id)
        group2 = Group(name="Group 2", created_by=user_b.id)
        db.add(group1)
        db.add(group2)
        await db.flush()

        # Group 1 的自訂分類
        cat1 = ExpenseCategory(
            name="category_for_group1",
            group_id=group1.id,
            created_by=user_a.id,
            is_default=False,
        )
        # Group 2 的自訂分類
        cat2 = ExpenseCategory(
            name="category_for_group2",
            group_id=group2.id,
            created_by=user_b.id,
            is_default=False,
        )
        db.add(cat1)
        db.add(cat2)
        await db.flush()

        # 查詢 Group 1
        resp = await client.get(
            "/api/v1/categories",
            headers=auth_header(user_a),
            params={"group_id": str(group1.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        names = [c["name"] for c in data]
        assert "category_for_group1" in names
        assert "category_for_group2" not in names

    async def test_list_requires_auth(self, client: AsyncClient):
        """無認證應回傳 403 (HTTPBearer 安全依賴)。"""
        resp = await client.get("/api/v1/categories")
        assert resp.status_code == 403


class TestCreateCategory:
    async def test_create_custom_category_for_group(
        self, client: AsyncClient, user_a, group_with_members
    ):
        """群組成員可建立自訂分類。"""
        resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_a),
            json={
                "name": "drinks",
                "icon": "coffee",
                "color": "#8B4513",
                "group_id": str(group_with_members.id),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "drinks"
        assert data["icon"] == "coffee"
        assert data["color"] == "#8B4513"
        assert data["is_default"] is False
        assert data["group_id"] == str(group_with_members.id)

    async def test_create_personal_category(self, client: AsyncClient, user_a):
        """不指定 group_id 也能建立個人分類。"""
        resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_a),
            json={"name": "personal", "icon": "user", "color": "#34495E"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "personal"
        assert data["icon"] == "user"
        assert data["is_default"] is False
        assert data["group_id"] is None

    async def test_create_category_minimal_fields(
        self, client: AsyncClient, user_a, group_with_members
    ):
        """只需 name，icon 和 color 可選。"""
        resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_a),
            json={
                "name": "minimal",
                "group_id": str(group_with_members.id),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "minimal"
        assert data["icon"] is None
        assert data["color"] is None

    async def test_create_category_non_member_forbidden(
        self, client: AsyncClient, user_c, group_with_members
    ):
        """非群組成員不可建立分類（403）。"""
        resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_c),
            json={
                "name": "secret",
                "group_id": str(group_with_members.id),
            },
        )
        assert resp.status_code == 403

    async def test_create_category_missing_name(
        self, client: AsyncClient, user_a, group_with_members
    ):
        """缺少 name 應回傳 422。"""
        resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_a),
            json={
                "icon": "test",
                "group_id": str(group_with_members.id),
            },
        )
        assert resp.status_code == 422

    async def test_create_category_invalid_group_id(self, client: AsyncClient, user_a):
        """使用不存在的 group_id 應回傳 403。"""
        fake_group_id = uuid.uuid4()
        resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_a),
            json={
                "name": "test",
                "group_id": str(fake_group_id),
            },
        )
        assert resp.status_code == 403

    async def test_create_category_without_auth(
        self, client: AsyncClient, group_with_members
    ):
        """無認證應回傳 403 (HTTPBearer 安全依賴)。"""
        resp = await client.post(
            "/api/v1/categories",
            json={
                "name": "test",
                "group_id": str(group_with_members.id),
            },
        )
        assert resp.status_code == 403


class TestDeleteCategory:
    async def test_delete_custom_category_by_creator(
        self, client: AsyncClient, db: AsyncSession, user_a
    ):
        """建立者可刪除自訂分類。"""
        cat = ExpenseCategory(
            name="to_delete",
            created_by=user_a.id,
            is_default=False,
        )
        db.add(cat)
        await db.flush()
        cat_id = cat.id

        resp = await client.delete(
            f"/api/v1/categories/{cat_id}", headers=auth_header(user_a)
        )
        assert resp.status_code == 204

        # 驗證確實已刪除
        result = await db.execute(select(ExpenseCategory).where(ExpenseCategory.id == cat_id))
        deleted_cat = result.scalar_one_or_none()
        assert deleted_cat is None

    async def test_delete_default_category_forbidden(
        self, client: AsyncClient, db: AsyncSession, user_a, default_categories
    ):
        """不可刪除預設分類。"""
        # 取第一個預設分類
        default_cat = default_categories[0]

        resp = await client.delete(
            f"/api/v1/categories/{default_cat.id}", headers=auth_header(user_a)
        )
        assert resp.status_code == 400
        assert "default" in resp.json()["detail"].lower()

        # 驗證仍然存在
        result = await db.execute(
            select(ExpenseCategory).where(ExpenseCategory.id == default_cat.id)
        )
        still_exists = result.scalar_one_or_none()
        assert still_exists is not None

    async def test_delete_by_non_creator_forbidden(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b
    ):
        """非建立者不可刪除分類。"""
        cat = ExpenseCategory(
            name="others_cat",
            created_by=user_a.id,
            is_default=False,
        )
        db.add(cat)
        await db.flush()

        resp = await client.delete(
            f"/api/v1/categories/{cat.id}", headers=auth_header(user_b)
        )
        assert resp.status_code == 403
        assert "creator" in resp.json()["detail"].lower() or "permission" in resp.json()["detail"].lower()

        # 驗證仍然存在
        result = await db.execute(
            select(ExpenseCategory).where(ExpenseCategory.id == cat.id)
        )
        still_exists = result.scalar_one_or_none()
        assert still_exists is not None

    async def test_delete_nonexistent_category(
        self, client: AsyncClient, user_a
    ):
        """刪除不存在的分類應回傳 404。"""
        fake_id = uuid.uuid4()
        resp = await client.delete(
            f"/api/v1/categories/{fake_id}", headers=auth_header(user_a)
        )
        assert resp.status_code == 404

    async def test_delete_without_auth(self, client: AsyncClient, db: AsyncSession, user_a):
        """無認證應回傳 403 (HTTPBearer 安全依賴)。"""
        cat = ExpenseCategory(
            name="test",
            created_by=user_a.id,
            is_default=False,
        )
        db.add(cat)
        await db.flush()

        resp = await client.delete(f"/api/v1/categories/{cat.id}")
        assert resp.status_code == 403


class TestCategoryIntegration:
    async def test_full_category_lifecycle(
        self, client: AsyncClient, db: AsyncSession, user_a, group_with_members, default_categories
    ):
        """完整的分類生命週期：列出 -> 建立 -> 查詢 -> 刪除。"""
        # 1. 列出預設分類
        resp = await client.get("/api/v1/categories", headers=auth_header(user_a))
        assert resp.status_code == 200
        initial_count = len(resp.json())

        # 2. 建立群組分類
        create_resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_a),
            json={
                "name": "Groceries",
                "icon": "shopping-cart",
                "color": "#27AE60",
                "group_id": str(group_with_members.id),
            },
        )
        assert create_resp.status_code == 201
        new_cat_id = create_resp.json()["id"]

        # 3. 列出分類含新建分類
        list_resp = await client.get(
            "/api/v1/categories",
            headers=auth_header(user_a),
            params={"group_id": str(group_with_members.id)},
        )
        assert list_resp.status_code == 200
        names = [c["name"] for c in list_resp.json()]
        assert "Groceries" in names
        assert len(list_resp.json()) == initial_count + 1

        # 4. 刪除分類
        delete_resp = await client.delete(
            f"/api/v1/categories/{new_cat_id}", headers=auth_header(user_a)
        )
        assert delete_resp.status_code == 204

        # 5. 驗證已刪除
        final_resp = await client.get(
            "/api/v1/categories",
            headers=auth_header(user_a),
            params={"group_id": str(group_with_members.id)},
        )
        final_names = [c["name"] for c in final_resp.json()]
        assert "Groceries" not in final_names

    async def test_multiple_groups_categories_isolation(
        self,
        client: AsyncClient,
        db: AsyncSession,
        user_a,
        user_b,
        group_with_members,
    ):
        """不同群組的分類應相互隔離。"""
        from app.models.group import Group, GroupMember

        # 建立第二個群組（user_b 為管理員）
        group2 = Group(name="Group 2", created_by=user_b.id)
        db.add(group2)
        await db.flush()

        member_b = GroupMember(group_id=group2.id, user_id=user_b.id, role="admin")
        db.add(member_b)
        await db.flush()

        # 在 group1 建立分類
        cat1_resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_a),
            json={
                "name": "group1_cat",
                "group_id": str(group_with_members.id),
            },
        )
        assert cat1_resp.status_code == 201

        # 在 group2 建立分類
        cat2_resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_b),
            json={
                "name": "group2_cat",
                "group_id": str(group2.id),
            },
        )
        assert cat2_resp.status_code == 201

        # user_a 查詢 group1 應只看到 group1_cat
        list1_resp = await client.get(
            "/api/v1/categories",
            headers=auth_header(user_a),
            params={"group_id": str(group_with_members.id)},
        )
        names1 = [c["name"] for c in list1_resp.json()]
        assert "group1_cat" in names1
        assert "group2_cat" not in names1

        # user_b 查詢 group2 應只看到 group2_cat
        list2_resp = await client.get(
            "/api/v1/categories",
            headers=auth_header(user_b),
            params={"group_id": str(group2.id)},
        )
        names2 = [c["name"] for c in list2_resp.json()]
        assert "group2_cat" in names2
        assert "group1_cat" not in names2

    async def test_create_category_with_empty_optional_fields(
        self, client: AsyncClient, user_a, group_with_members
    ):
        """可以建立只有 name 的分類，icon 和 color 為空。"""
        resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_a),
            json={
                "name": "minimal_category",
                "group_id": str(group_with_members.id),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "minimal_category"
        assert data["icon"] is None
        assert data["color"] is None
        assert data["is_default"] is False

    async def test_category_response_fields(
        self, client: AsyncClient, user_a, group_with_members
    ):
        """驗證分類回應包含所有必要欄位。"""
        resp = await client.post(
            "/api/v1/categories",
            headers=auth_header(user_a),
            json={
                "name": "test_category",
                "icon": "test",
                "color": "#FFFFFF",
                "group_id": str(group_with_members.id),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        # 驗證所有必要欄位存在
        assert "id" in data
        assert "name" in data
        assert "icon" in data
        assert "color" in data
        assert "is_default" in data
        assert "group_id" in data
        assert "created_at" in data
