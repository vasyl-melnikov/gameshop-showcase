import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app  # Import FastAPI app instance
from app.dto_schemas.game_change_request import GameChangeRequestResponseModel
from app.dto_schemas.user import UserRolePatch
from app.dto_schemas.steam_guard import SetSteamGuardCodeRequest
from app.db.managers.exceptions import UserNotFound, ChangeRequestNotFound, \
    GameNotFound, ChangeRequestNotPending
from app.db.models import GameChangeRequest
from app.dto_schemas.auth import Roles

# Set up the TestClient for FastAPI
client = TestClient(app)


@pytest.mark.asyncio
async def test_patch_user_role():
    # Mock dependencies
    mock_get_user_by_email = MagicMock(
        return_value={"id": 1, "role": Roles.USER})
    mock_update_role_by_email = MagicMock(
        return_value={"id": 1, "role": Roles.ADMIN})

    # Patch the dependencies
    with patch("app.api.admin.get_user_by_email", mock_get_user_by_email), \
            patch("app.api.admin.update_role_by_email",
                  mock_update_role_by_email):
        # Create a valid UserRolePatch request body
        user_role_patch = UserRolePatch(email="testuser@example.com",
                                        role=Roles.ADMIN)

        # Send the PATCH request to update the user's role
        response = client.patch(
            "/admins/me/users/role", json=user_role_patch.dict(),
            headers={"Authorization": "Bearer test_token"}
        )

        # Ensure the response is as expected
        assert response.status_code == 200
        assert response.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_confirm_game_change_request():
    # Mock dependencies
    mock_approve_game_change_request = MagicMock(
        return_value=("game", "old_game"))
    mock_delete_s3_object = MagicMock()

    # Patch the dependencies
    with patch("app.api.admin.approve_game_change_request",
               mock_approve_game_change_request), \
            patch("app.api.admin.S3Client.delete_object",
                  mock_delete_s3_object):
        # Send the POST request to approve a game change request
        response = client.post(
            "/admins/me/moderator-requests/1/approve",
            headers={"Authorization": "Bearer test_token"}
        )

        # Ensure the response is as expected
        assert response.status_code == 200
        assert "id" in response.json()


@pytest.mark.asyncio
async def test_reject_game_change_request():
    # Mock dependencies
    mock_disapprove_game_change_request = MagicMock(
        return_value={"id": 1, "changes": {"game_img_url": "image_url"}})
    mock_delete_s3_object = MagicMock()

    # Patch the dependencies
    with patch("app.api.admin.disapprove_game_change_request",
               mock_disapprove_game_change_request), \
            patch("app.api.admin.S3Client.delete_object",
                  mock_delete_s3_object):
        # Send the POST request to reject a game change request
        response = client.post(
            "/admins/me/moderator-requests/1/disapprove",
            headers={"Authorization": "Bearer test_token"}
        )

        # Ensure the response is as expected
        assert response.status_code == 200
        assert response.json()["id"] == 1


@pytest.mark.asyncio
async def test_get_recent_game_change_requests():
    # Mock dependencies
    mock_get_game_change_requests = MagicMock(
        return_value=[{"id": 1, "changes": {"game_img_url": "image_url"}}])

    # Patch the dependencies
    with patch("app.api.admin.get_game_change_requests",
               mock_get_game_change_requests):
        # Send the GET request to fetch recent game change requests
        response = client.get(
            "/admins/me/moderator-requests",
            headers={"Authorization": "Bearer test_token"}
        )

        # Ensure the response is as expected
        assert response.status_code == 200
        assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_fetch_pending_requests():
    # Mock dependencies
    mock_redis_client = MagicMock()
    mock_redis_client.scan_iter = MagicMock(
        return_value=["SG_REQUEST_PREFIX:1"])
    mock_redis_client.get = MagicMock(return_value={"status": "pending"})

    # Patch the dependencies
    with patch("app.api.admin.get_redis_client",
               return_value=mock_redis_client):
        # Send the GET request to fetch pending steam guard requests
        response = client.get(
            "/admins/me/steam-guard-requests",
            headers={"Authorization": "Bearer test_token"}
        )

        # Ensure the response is as expected
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_set_steam_guard_code():
    # Mock dependencies
    mock_redis_client = MagicMock()
    mock_redis_client.exists = MagicMock(return_value=True)
    mock_redis_client.set = MagicMock()

    # Patch the dependencies
    with patch("app.api.admin.get_redis_client",
               return_value=mock_redis_client):
        # Create a valid SetSteamGuardCodeRequest body
        set_steam_guard_code_request = SetSteamGuardCodeRequest(code="123456")

        # Send the POST request to set the Steam Guard code
        response = client.post(
            "/admins/me/steam-guard-requests/1",
            json=set_steam_guard_code_request.dict(),
            headers={"Authorization": "Bearer test_token"}
        )

        # Ensure the response is as expected
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_patch_user_role_user_not_found():
    # Mock dependencies to simulate user not found
    mock_get_user_by_email = MagicMock(side_effect=UserNotFound)

    # Patch the dependencies
    with patch("app.api.admin.get_user_by_email", mock_get_user_by_email):
        # Create a valid UserRolePatch request body
        user_role_patch = UserRolePatch(email="nonexistent@example.com",
                                        role=Roles.ADMIN)

        # Send the PATCH request
        response = client.patch(
            "/admins/me/users/role", json=user_role_patch.dict(),
            headers={"Authorization": "Bearer test_token"}
        )

        # Ensure the response is a 404 error
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
