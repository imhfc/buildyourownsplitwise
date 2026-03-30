import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestSendFriendRequest:
    async def test_send_request_success(self, client: AsyncClient, user_a: User, user_b: User):
        resp = await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "bob@example.com"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["user"]["email"] == "bob@example.com"

    async def test_send_request_to_self(self, client: AsyncClient, user_a: User):
        resp = await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "alice@example.com"},
        )
        assert resp.status_code == 400

    async def test_send_request_user_not_found(self, client: AsyncClient, user_a: User):
        resp = await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "nobody@example.com"},
        )
        assert resp.status_code == 404

    async def test_send_duplicate_request(self, client: AsyncClient, user_a: User, user_b: User):
        await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "bob@example.com"},
        )
        resp = await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "bob@example.com"},
        )
        assert resp.status_code == 409

    async def test_no_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/friends/requests",
            json={"friend_email": "bob@example.com"},
        )
        assert resp.status_code == 403


class TestListPendingRequests:
    async def test_list_incoming_requests(self, client: AsyncClient, user_a: User, user_b: User):
        # A sends request to B
        await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "bob@example.com"},
        )
        # B sees it
        resp = await client.get("/api/v1/friends/requests", headers=auth_header(user_b))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["user"]["email"] == "alice@example.com"

    async def test_sender_does_not_see_own_request(self, client: AsyncClient, user_a: User, user_b: User):
        await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "bob@example.com"},
        )
        resp = await client.get("/api/v1/friends/requests", headers=auth_header(user_a))
        assert resp.status_code == 200
        assert len(resp.json()) == 0


class TestRespondToRequest:
    async def test_accept_request(self, client: AsyncClient, user_a: User, user_b: User):
        # A sends request to B
        send_resp = await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "bob@example.com"},
        )
        request_id = send_resp.json()["id"]

        # B accepts
        resp = await client.patch(
            f"/api/v1/friends/requests/{request_id}",
            headers=auth_header(user_b),
            json={"action": "accept"},
        )
        assert resp.status_code == 204

        # Both should now see each other in friends list
        friends_a = await client.get("/api/v1/friends", headers=auth_header(user_a))
        assert len(friends_a.json()) == 1
        assert friends_a.json()[0]["friend"]["email"] == "bob@example.com"

        friends_b = await client.get("/api/v1/friends", headers=auth_header(user_b))
        assert len(friends_b.json()) == 1
        assert friends_b.json()[0]["friend"]["email"] == "alice@example.com"

    async def test_reject_request(self, client: AsyncClient, user_a: User, user_b: User):
        send_resp = await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "bob@example.com"},
        )
        request_id = send_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/friends/requests/{request_id}",
            headers=auth_header(user_b),
            json={"action": "reject"},
        )
        assert resp.status_code == 204

        # Neither should see each other in friends list
        friends_a = await client.get("/api/v1/friends", headers=auth_header(user_a))
        assert len(friends_a.json()) == 0

    async def test_wrong_user_cannot_respond(self, client: AsyncClient, user_a: User, user_b: User, user_c: User):
        send_resp = await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "bob@example.com"},
        )
        request_id = send_resp.json()["id"]

        # C tries to respond to A->B request
        resp = await client.patch(
            f"/api/v1/friends/requests/{request_id}",
            headers=auth_header(user_c),
            json={"action": "accept"},
        )
        assert resp.status_code == 403

    async def test_invalid_action(self, client: AsyncClient, user_a: User, user_b: User):
        send_resp = await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "bob@example.com"},
        )
        request_id = send_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/friends/requests/{request_id}",
            headers=auth_header(user_b),
            json={"action": "maybe"},
        )
        assert resp.status_code == 400


class TestRemoveFriend:
    async def test_remove_friend(self, client: AsyncClient, user_a: User, user_b: User):
        # Become friends
        send_resp = await client.post(
            "/api/v1/friends/requests",
            headers=auth_header(user_a),
            json={"friend_email": "bob@example.com"},
        )
        request_id = send_resp.json()["id"]
        await client.patch(
            f"/api/v1/friends/requests/{request_id}",
            headers=auth_header(user_b),
            json={"action": "accept"},
        )

        # Remove
        resp = await client.delete(
            f"/api/v1/friends/{user_b.id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 204

        # No longer friends
        friends_a = await client.get("/api/v1/friends", headers=auth_header(user_a))
        assert len(friends_a.json()) == 0

    async def test_remove_nonexistent_friend(self, client: AsyncClient, user_a: User):
        resp = await client.delete(
            f"/api/v1/friends/{uuid.uuid4()}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 404


class TestSearchUsers:
    async def test_search_by_email(self, client: AsyncClient, user_a: User, user_b: User):
        resp = await client.get(
            "/api/v1/friends/search?q=bob",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["user"]["email"] == "bob@example.com"
        assert data[0]["is_friend"] is False

    async def test_search_excludes_self(self, client: AsyncClient, user_a: User):
        resp = await client.get(
            "/api/v1/friends/search?q=alice",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    async def test_search_no_results(self, client: AsyncClient, user_a: User):
        resp = await client.get(
            "/api/v1/friends/search?q=zzzzz",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 0
