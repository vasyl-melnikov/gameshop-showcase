import importlib

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, ANY, AsyncMock

from redis.asyncio import Redis

from app.api.user import DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE, \
    EMAIL_REQUEST_PREFIX, PASSWORD_RESET_REQUEST_PREFIX, \
    TEMPORARY_PASSWORD_RESET_TOKEN_LENGTH, SETUP_2FA_REQUEST_PREFIX
from app.business_logic.auth import hash_password, verify_password
from app.main import app
from app.db.models import User, Order
from app.dto_schemas.user import UserCreate, UserUpdatePersonalInfo, \
    UserResponseModel, UserRoleResponseModel
from app.dto_schemas.auth import TokenData, Roles
from app.dto_schemas.order import OrderResponseModel
from app.redis_cache import get_redis_client
from app.email_sender import EmailSender, get_email_sender
from app.s3 import get_s3_client

client = TestClient(app)


def mock_dependency(mock):
    yield mock


redis_mock = AsyncMock()
s3_mock = AsyncMock()
email_sender = AsyncMock()

app.dependency_overrides[get_redis_client] = lambda: (yield redis_mock)
app.dependency_overrides[get_s3_client] = lambda: (yield s3_mock)
app.dependency_overrides[get_email_sender] = lambda: (yield email_sender)


def reload_user_module():
    from app.api import user
    importlib.reload(user)


@pytest.fixture
def mock_get_user_by_ukey():
    with patch("app.db.managers.user_manager.get_user_by_ukey",
               autospec=True) as mock_get_user:
        reload_user_module()
        yield mock_get_user


@pytest.fixture
def mock_get_user_by_email():
    with patch("app.db.managers.user_manager.get_user_by_email",
               autospec=True) as mock_get_user:
        reload_user_module()
        yield mock_get_user


@pytest.fixture
def mock_token_data():
    with patch("app.api.common.verify_token_access",
               autospec=True) as mock_token_data:
        reload_user_module()
        yield mock_token_data


@pytest.fixture
def mock_get_orders_by_user_id():
    with patch("app.db.managers.orders.get_orders_by_user_id",
               autospec=True) as mock_get_orders:
        reload_user_module()
        yield mock_get_orders


mock_user = User(
    first_name="first_name",
    last_name="last_name",
    username="username",
    email="email@example.com",
    ukey="ASDVASD12",
    role=Roles.USER,
    mfa_enabled=False
)


# Test Get User
def test_get_user(mock_get_user_by_ukey, mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey

    mock_get_user_by_ukey.return_value = mock_user
    mock_token_data.return_value = token_data

    response = client.get("/api/v1/users/me",
                          headers={"Authorization": "Bearer test_token"})

    assert response.status_code == 200
    assert response.json()["ukey"] == mock_user.ukey


def test_get_user_not_found(mock_get_user_by_ukey, mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey

    mock_get_user_by_ukey.return_value = None
    mock_token_data.return_value = token_data

    response = client.get("/api/v1/users/me",
                          headers={"Authorization": "Bearer test_token"})

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"


# Test Update User Information
@patch("app.api.user.update_user")
def test_update_user_personal_info(user_update_mock, mock_get_user_by_ukey,
                                   mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey

    mock_get_user_by_ukey.return_value = mock_user
    mock_token_data.return_value = token_data

    user_info = {"first_name": "John", "last_name": "Doe"}
    response = client.patch(
        "/api/v1/users/me", json=user_info,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == user_info["first_name"]
    assert response.json()["last_name"] == user_info["last_name"]
    user_update_mock.assert_called_once_with(ANY, mock_user)


@patch("app.api.user.update_user")
def test_update_user_personal_info_not_found(user_update_mock,
                                             mock_get_user_by_ukey,
                                             mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey

    mock_get_user_by_ukey.return_value = None
    mock_token_data.return_value = token_data

    user_info = {"first_name": "John", "last_name": "Doe"}
    response = client.patch(
        "/api/v1/users/me", json=user_info,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"
    user_update_mock.assert_not_called()


@patch("app.api.user.verify_password")
@patch("app.api.user.generate_random_mfa_code")
@patch("app.api.user.generate_redis_key")
@patch("app.api.user.hash_password")
def test_password_change_request_success(
        mock_hash_password,
        mock_generate_redis_key,
        mock_generate_random_mfa_code,
        mock_verify_password,
        mock_get_user_by_ukey,
        mock_token_data,
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey
    mock_token_data.return_value = token_data
    mock_get_user_by_ukey.return_value = mock_user
    mock_verify_password.return_value = True
    mock_generate_random_mfa_code.return_value = "123456"
    mock_generate_redis_key.return_value = "redis-key"
    mock_hash_password.return_value = "hashed-new-password"

    payload = {"old_password": "SuperOld214", "new_password": "SuperNew214"}
    response = client.post(
        "/api/v1/users/me/request_change_password",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    redis_mock.setex.assert_called_once_with(
        "redis-key", DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE, "hashed-new-password"
    )


@patch("app.api.user.verify_password")
def test_password_change_request_no_token_ukey(
        mock_verify_password, mock_get_user_by_ukey, mock_token_data
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = None  # No ukey in token data
    mock_token_data.return_value = token_data

    payload = {"old_password": "SuperOld214", "new_password": "SuperNew214"}
    response = client.post(
        "/api/v1/users/me/request_change_password",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    mock_get_user_by_ukey.assert_not_called()
    mock_verify_password.assert_not_called()


@patch("app.api.user.verify_password")
def test_password_change_request_user_not_found(
        mock_verify_password, mock_get_user_by_ukey, mock_token_data
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey
    mock_token_data.return_value = token_data
    mock_get_user_by_ukey.return_value = None  # Simulate user not found

    payload = {"old_password": "SuperOld214", "new_password": "SuperNew214"}
    response = client.post(
        "/api/v1/users/me/request_change_password",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"
    mock_verify_password.assert_not_called()


@patch("app.api.user.verify_password")
def test_password_change_request_invalid_password(
        mock_verify_password, mock_get_user_by_ukey, mock_token_data
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey
    mock_token_data.return_value = token_data
    mock_get_user_by_ukey.return_value = mock_user
    mock_verify_password.return_value = False  # Simulate invalid password

    payload = {"old_password": "SuperOld2141", "new_password": "SuperNew214"}
    response = client.post(
        "/api/v1/users/me/request_change_password",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Old password is wrong"


@patch("app.api.user.verify_password")
def test_password_change_request_unexpected_error(
        mock_verify_password, mock_get_user_by_ukey, mock_token_data
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey
    mock_token_data.return_value = token_data
    mock_get_user_by_ukey.side_effect = Exception("Unexpected error")

    payload = {"old_password": "SuperOld214", "new_password": "SuperNew214"}
    with pytest.raises(Exception) as exc:
        client.post(
            "/api/v1/users/me/request_change_password",
            json=payload,
            headers={"Authorization": "Bearer test_token"},
        )

    assert exc.value.status_code == 500
    assert "Error has occurred on a server side" in exc.value.detail


# Test Case: Redis key not found
@patch("app.api.user.get_user_by_ukey")
@patch("app.api.user.update_user")
def test_change_password_redis_key_not_found(
        mock_update_user, mock_get_user_by_ukey, mock_token_data
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey
    mock_token_data.return_value = token_data
    redis_mock.get.return_value = None  # Simulate Redis key not found

    payload = {"code": "mfa_code"}
    response = client.patch(
        "/api/v1/users/me/change_password",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    mock_get_user_by_ukey.assert_not_called()
    mock_update_user.assert_not_called()


# Test Case: Token data ukey is None
@patch("app.api.user.get_user_by_ukey")
@patch("app.api.user.update_user")
def test_change_password_no_token_ukey(
        mock_update_user, mock_get_user_by_ukey, mock_token_data,
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = None  # Simulate missing ukey
    mock_token_data.return_value = token_data
    redis_mock.get.return_value = b"hashed-new-password"  # Simulate Redis key found

    payload = {"code": "mfa_code"}
    response = client.patch(
        "/api/v1/users/me/change_password",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    mock_get_user_by_ukey.assert_not_called()
    mock_update_user.assert_not_called()


# Test Case: User not found
@patch("app.api.user.get_user_by_ukey")
@patch("app.api.user.update_user")
def test_change_password_user_not_found(
        mock_update_user, mock_get_user_by_ukey, mock_token_data
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey
    mock_token_data.return_value = token_data
    redis_mock.get.return_value = b"hashed-new-password"  # Simulate Redis key found
    mock_get_user_by_ukey.return_value = None  # Simulate user not found

    payload = {"code": "mfa_code"}
    response = client.patch(
        "/api/v1/users/me/change_password",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"
    mock_update_user.assert_not_called()


# Test Case: Successful password change
@patch("app.api.user.get_user_by_ukey")
@patch("app.api.user.update_user")
def test_change_password_success(
        mock_update_user, mock_get_user_by_ukey, mock_token_data,
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey
    mock_token_data.return_value = token_data
    redis_mock.get.return_value = b"hashed-new-password"  # Simulate Redis key found
    mock_get_user_by_ukey.return_value = mock_user  # Simulate user found
    mock_update_user.return_value = mock_user

    payload = {"code": "mfa_code"}
    response = client.patch(
        "/api/v1/users/me/change_password",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    assert response.json()["ukey"] == mock_user.ukey
    mock_update_user.assert_called_once_with(ANY, mock_user)


# Test Case: Unexpected error
@patch("app.api.user.get_user_by_ukey")
@patch("app.api.user.update_user")
def test_change_password_unexpected_error(
        mock_update_user, mock_get_user_by_ukey, mock_token_data,
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = mock_user.ukey
    mock_token_data.return_value = token_data
    redis_mock.get.return_value = b"hashed-new-password"  # Simulate Redis key found
    mock_get_user_by_ukey.side_effect = Exception(
        "Unexpected error")  # Simulate database failure

    payload = {"code": "mfa_code"}
    with pytest.raises(Exception) as exc:
        client.patch(
            "/api/v1/users/me/change_password",
            json=payload,
            headers={"Authorization": "Bearer test_token"},
        )

    assert exc.value.status_code == 500
    assert "Error has occurred on a server side" in exc.value.detail
    mock_update_user.assert_not_called()


# Test Case: Successful email change request
def test_change_email_request_success(mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"  # Simulate valid ukey
    mock_token_data.return_value = token_data
    redis_mock.setex.return_value = None  # Simulate Redis success

    payload = {"email": "newemail@example.com"}
    response = client.post(
        "/api/v1/users/me/request_change_email",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    redis_mock.setex.assert_called_once_with(
        ANY, DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE, payload["email"]
    )


# Test Case: Redis error
def test_change_email_request_redis_error(mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"  # Simulate valid ukey
    mock_token_data.return_value = token_data
    redis_mock.setex.side_effect = Exception(
        "Redis error")  # Simulate Redis failure

    payload = {"email": "newemail@example.com"}
    with pytest.raises(Exception) as exc:
        client.post(
            "/api/v1/users/me/request_change_email",
            json=payload,
            headers={"Authorization": "Bearer test_token"},
        )

    assert exc.value.status_code == 500
    assert "Error has occurred on a server side" in exc.value.detail
    redis_mock.setex.assert_called_once_with(
        ANY, DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE, payload["email"]
    )


# Test Case: redis_client.get returns None
def test_change_email_invalid_mfa_code(mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"
    mock_token_data.return_value = token_data

    redis_mock.get.return_value = None  # Simulate invalid MFA code

    payload = {"code": "invalid_code"}
    response = client.patch(
        "/api/v1/users/me/change_email",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    redis_mock.get.assert_called_once_with(
        f"{EMAIL_REQUEST_PREFIX}:{token_data.ukey}:{payload['code']}"
    )


# Test Case: token_data.ukey is None
def test_change_email_no_token_ukey(mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = None  # Simulate missing ukey
    mock_token_data.return_value = token_data

    payload = {"code": "valid_code"}
    response = client.patch(
        "/api/v1/users/me/change_email",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    redis_mock.get.assert_not_called()


# Test Case: User not found
@patch("app.api.user.get_user_by_ukey")
def test_change_email_user_not_found(mock_get_user_by_ukey,
                                     mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"
    mock_token_data.return_value = token_data

    redis_mock.get.return_value = b"newemail@example.com"  # Simulate valid Redis key
    mock_get_user_by_ukey.return_value = None  # Simulate user not found

    payload = {"code": "valid_code"}
    response = client.patch(
        "/api/v1/users/me/change_email",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"
    redis_mock.get.assert_called_once_with(
        f"{EMAIL_REQUEST_PREFIX}:{token_data.ukey}:{payload['code']}"
    )
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)


# Test Case: Successful email update
@patch("app.api.user.update_user")
@patch("app.api.user.get_user_by_ukey")
def test_change_email_success(mock_get_user_by_ukey, mock_update_user,
                              mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"
    mock_token_data.return_value = token_data

    redis_mock.get.return_value = b"newemail@example.com"  # Simulate valid Redis key
    mock_get_user_by_ukey.return_value = mock_user

    payload = {"code": "valid_code"}
    response = client.patch(
        "/api/v1/users/me/change_email",
        json=payload,
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "newemail@example.com"
    redis_mock.get.assert_called_once_with(
        f"{EMAIL_REQUEST_PREFIX}:{token_data.ukey}:{payload['code']}"
    )
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)
    mock_update_user.assert_called_once_with(ANY, mock_user)
    assert mock_user.email == "newemail@example.com"


# Test Case: User not found
@patch("app.api.user.get_user_by_email")
def test_reset_user_password_request_user_not_found(mock_get_user_by_email):
    mock_get_user_by_email.return_value = None  # Simulate user not found

    payload = {"email": "nonexistent@example.com"}
    response = client.post("/api/v1/users/request_password_reset", json=payload)

    assert response.status_code == 200
    assert response.json() == {}  # Empty response
    mock_get_user_by_email.assert_called_once_with(ANY, payload["email"])
    redis_mock.setex.assert_not_called()


# Test Case: Successful password reset token generation
@patch("app.api.user.get_user_by_email")
@patch("app.api.user.generate_string")
def test_reset_user_password_request_success(mock_generate_string,
                                             mock_get_user_by_email,
                                             ):
    mock_get_user_by_email.return_value = mock_user

    reset_token = "mock_reset_token"
    mock_generate_string.return_value = reset_token

    payload = {"email": mock_user.email}
    response = client.post("/api/v1/users/request_password_reset", json=payload)

    assert response.status_code == 200
    mock_get_user_by_email.assert_called_once_with(ANY, payload["email"])
    mock_generate_string.assert_called_once_with(
        TEMPORARY_PASSWORD_RESET_TOKEN_LENGTH)
    redis_mock.setex.assert_called_once_with(
        f"{PASSWORD_RESET_REQUEST_PREFIX}:{None}:{reset_token}",
        DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE,
        mock_user.email,
    )


# Test Case: Redis error during `setex`
@patch("app.api.user.get_user_by_email")
@patch("app.api.user.generate_string")
def test_reset_user_password_request_redis_error(mock_generate_string,
                                                 mock_get_user_by_email
                                                 ):
    mock_user = MagicMock(spec=User)
    mock_user.email = "user@example.com"
    mock_get_user_by_email.return_value = mock_user

    reset_token = "mock_reset_token"
    mock_generate_string.return_value = reset_token

    redis_mock.setex.side_effect = Exception(
        "Redis error")  # Simulate Redis failure

    payload = {"email": mock_user.email}
    with pytest.raises(Exception) as exc:
        client.post("/api/v1/users/request_password_reset", json=payload)

    assert exc.value.status_code == 500
    assert "Error has occurred on a server side" in exc.value.detail
    mock_get_user_by_email.assert_called_once_with(ANY, payload["email"])
    mock_generate_string.assert_called_once_with(
        TEMPORARY_PASSWORD_RESET_TOKEN_LENGTH)
    redis_mock.setex.assert_called_once_with(
        f"{PASSWORD_RESET_REQUEST_PREFIX}:{None}:{reset_token}",
        DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE,
        mock_user.email,
    )


# Test Case: Email field validation
def test_reset_user_password_request_invalid_email():
    payload = {"email": "invalid-email-format"}
    response = client.post("/api/v1/users/request_password_reset", json=payload)

    assert response.status_code == 422  # Validation error
    assert "email" in response.json()["detail"][0]["loc"]


# Test Case: Debug print of the token
@patch("app.api.user.get_user_by_email")
@patch("app.api.user.generate_string")
def test_reset_user_password_request_debug_token(mock_generate_string,
                                                 mock_get_user_by_email,
                                                 capsys):
    mock_user = MagicMock(spec=User)
    mock_user.email = "user@example.com"
    mock_get_user_by_email.return_value = mock_user

    reset_token = "mock_reset_token"
    mock_generate_string.return_value = reset_token

    payload = {"email": mock_user.email}
    response = client.post("/api/v1/users/request_password_reset", json=payload)

    assert response.status_code == 200

    captured = capsys.readouterr()
    assert reset_token in captured.out  # Ensure token was printed for debugging


# Test Case: Token not found in Redis
def test_reset_user_pass_token_not_found():
    redis_mock.get.return_value = None  # Simulate Redis key not found

    reset_pass_token = "invalid_token"
    payload = {"password": "OldPass123"}
    response = client.patch(
        f"/api/v1/users/reset_password/{reset_pass_token}",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    redis_mock.get.assert_called_once_with(
        f"{PASSWORD_RESET_REQUEST_PREFIX}:{None}:{reset_pass_token}"
    )


# Test Case: User not found
def test_reset_user_pass_user_not_found(mock_get_user_by_email):
    redis_mock.get.return_value = b"user@example.com"  # Valid Redis key
    mock_get_user_by_email.return_value = None  # Simulate user not found in DB

    reset_pass_token = "valid_token"
    payload = {"password": "OldPass123"}
    response = client.patch(
        f"/api/v1/users/reset_password/{reset_pass_token}",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"
    redis_mock.get.assert_called_once_with(
        f"{PASSWORD_RESET_REQUEST_PREFIX}:{None}:{reset_pass_token}"
    )
    mock_get_user_by_email.assert_called_once_with(ANY, "user@example.com")


# Test Case: Successful password reset
@patch("app.api.user.update_user")
def test_reset_user_pass_success(mock_update_user,
                                 mock_get_user_by_email):
    mock_get_user_by_email.return_value = mock_user
    redis_mock.get.return_value = b"user@example.com"  # Valid Redis key

    reset_pass_token = "valid_token"
    payload = {"password": "Kdmsaasd132"}
    response = client.patch(
        f"/api/v1/users/reset_password/{reset_pass_token}",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["email"] == mock_user.email
    redis_mock.get.assert_called_once_with(
        f"{PASSWORD_RESET_REQUEST_PREFIX}:{None}:{reset_pass_token}"
    )
    mock_get_user_by_email.assert_called_once_with(ANY, "user@example.com")
    mock_update_user.assert_called_once_with(ANY, mock_user)
    assert verify_password(payload["password"], mock_user.hashed_password)


# Test Case: Redis error during `get`
def test_reset_user_pass_redis_error():
    redis_mock.get.side_effect = Exception(
        "Redis error")  # Simulate Redis failure

    reset_pass_token = "valid_token"
    payload = {"password": "KDMSa123d"}

    with pytest.raises(Exception) as exc:
        client.patch(
            f"/api/v1/users/reset_password/{reset_pass_token}",
            json=payload,
        )

    assert exc.value.status_code == 500
    assert "Error has occurred on a server side" in exc.value.detail


# Test Case: Validation error for password
def test_reset_user_pass_validation_error():
    reset_pass_token = "valid_token"
    payload = {"password": ""}  # Invalid password
    response = client.patch(
        f"/api/v1/users/reset_password/{reset_pass_token}",
        json=payload,
    )

    assert response.status_code == 422  # Unprocessable Entity
    assert "password" in response.json()["detail"][0]["loc"]


# Test Case: User not found
def test_request_enable_2fa_user_not_found(mock_get_user_by_ukey, mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"
    mock_token_data.return_value = token_data

    mock_get_user_by_ukey.return_value = None  # Simulate user not found

    response = client.post(
        "/api/v1/users/me/request_enable_2fa",
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)


# Test Case: MFA already enabled
def test_request_enable_2fa_mfa_already_enabled(mock_get_user_by_ukey, mock_token_data):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"
    mock_token_data.return_value = token_data

    mock_user = MagicMock(spec=User)
    mock_user.mfa_enabled = True  # Simulate MFA already enabled
    mock_get_user_by_ukey.return_value = mock_user

    response = client.post(
        "/api/v1/users/me/request_enable_2fa",
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "MFA is already enabled"
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)


# Test Case: Successfully generates MFA code
@patch("app.api.user.generate_random_mfa_code", return_value="123456")
def test_request_enable_2fa_success(
        mock_generate_random_mfa_code, mock_get_user_by_ukey, mock_token_data
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"
    token_data.email = "user@example.com"
    mock_token_data.return_value = token_data

    mock_user.mfa_enabled = False  # Simulate MFA not enabled
    mock_get_user_by_ukey.return_value = mock_user

    response = client.post(
        "/api/v1/users/me/request_enable_2fa",
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    redis_mock.setex.assert_called_once_with(
        f"{SETUP_2FA_REQUEST_PREFIX}:{token_data.ukey}:123456",
        DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE,
        token_data.email,
    )
    mock_generate_random_mfa_code.assert_called_once()
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)


# Test Case: Redis error during `setex`
@patch("app.db.managers.user_manager.get_user_by_ukey")
@patch("app.redis_cache.get_redis_client")
@patch("app.api.user.generate_random_mfa_code", return_value="123456")
def test_request_enable_2fa_redis_error(
        mock_generate_random_mfa_code, mock_redis_client, mock_get_user_by_ukey
):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"
    token_data.email = "user@example.com"

    mock_user = MagicMock(spec=User)
    mock_user.mfa_enabled = False  # Simulate MFA not enabled
    mock_get_user_by_ukey.return_value = mock_user

    mock_redis_client.return_value.setex.side_effect = Exception("Redis error")

    response = client.post(
        "/api/v1/users/me/request_enable_2fa",
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 500
    assert "Internal Server Error" in response.text
    mock_redis_client.return_value.setex.assert_called_once_with(
        f"{SETUP_2FA_REQUEST_PREFIX}:{token_data.ukey}:123456",
        DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE,
        token_data.email,
    )
    mock_generate_random_mfa_code.assert_called_once()
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)


# Test Case: Token data is invalid
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_request_enable_2fa_invalid_token_data(mock_get_user_by_ukey,
                                               mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = None  # Simulate missing `ukey`

    response = client.post(
        "/api/v1/users/me/request_enable_2fa",
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    mock_get_user_by_ukey.assert_not_called()
    mock_redis_client.return_value.setex.assert_not_called()


# Test Case: Redis key does not exist for the MFA code
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_enable_2fa_key_not_found(mock_get_user_by_ukey, mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_redis_client.return_value.get.return_value = None  # Key not found

    response = client.patch(
        "/api/v1/users/me/enable_2fa",
        json={"code": "123456"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    mock_get_user_by_ukey.assert_not_called()
    mock_redis_client.return_value.get.assert_called_once_with(
        f"{SETUP_2FA_REQUEST_PREFIX}:{token_data.ukey}:123456"
    )


# Test Case: `token_data.ukey` is None
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_enable_2fa_invalid_token_data(mock_get_user_by_ukey,
                                       mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = None  # Simulate missing ukey

    response = client.patch(
        "/api/v1/users/me/enable_2fa",
        json={"code": "123456"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    mock_get_user_by_ukey.assert_not_called()
    mock_redis_client.return_value.get.assert_not_called()


# Test Case: User is not found
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_enable_2fa_user_not_found(mock_get_user_by_ukey, mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_redis_client.return_value.get.return_value = b"user@example.com"  # Simulate key found
    mock_get_user_by_ukey.return_value = None  # User not found

    response = client.patch(
        "/api/v1/users/me/enable_2fa",
        json={"code": "123456"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)


# Test Case: Successfully enable 2FA
@patch("app.api.user.update_user")
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_enable_2fa_success(mock_get_user_by_ukey, mock_redis_client,
                            mock_update_user):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_user = MagicMock(spec=User)
    mock_user.mfa_enabled = False
    mock_get_user_by_ukey.return_value = mock_user  # Simulate valid user

    mock_redis_client.return_value.get.return_value = b"user@example.com"  # Key found

    response = client.patch(
        "/api/v1/users/me/enable_2fa",
        json={"code": "123456"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    assert response.json()["mfa_enabled"] is True
    mock_redis_client.return_value.get.assert_called_once_with(
        f"{SETUP_2FA_REQUEST_PREFIX}:{token_data.ukey}:123456"
    )
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)
    mock_update_user.assert_called_once_with(ANY, mock_user)


# Test Case: Redis error
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_enable_2fa_redis_error(mock_get_user_by_ukey, mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_redis_client.return_value.get.side_effect = Exception("Redis error")

    response = client.patch(
        "/api/v1/users/me/enable_2fa",
        json={"code": "123456"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 500
    assert "Internal Server Error" in response.text
    mock_redis_client.return_value.get.assert_called_once_with(
        f"{SETUP_2FA_REQUEST_PREFIX}:{token_data.ukey}:123456"
    )
    mock_get_user_by_ukey.assert_not_called()


# Test Case: User not found
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_request_disable_2fa_user_not_found(mock_get_user_by_ukey,
                                            mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_get_user_by_ukey.return_value = None  # User not found

    response = client.post(
        "/api/v1/users/me/request_disable_2fa",
        json={},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)


# Test Case: MFA is already disabled
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_request_disable_2fa_mfa_already_disabled(mock_get_user_by_ukey,
                                                  mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_user = MagicMock(spec=User)
    mock_user.mfa_enabled = False  # MFA already disabled
    mock_get_user_by_ukey.return_value = mock_user

    response = client.post(
        "/api/v1/users/me/request_disable_2fa",
        json={},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "MFA is already disabled"
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)
    mock_redis_client.setex.assert_not_called()


# Test Case: Successfully request to disable MFA
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_request_disable_2fa_success(mock_get_user_by_ukey, mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_user = MagicMock(spec=User)
    mock_user.mfa_enabled = True  # MFA enabled
    mock_get_user_by_ukey.return_value = mock_user

    mock_redis_client.return_value.setex.return_value = None  # Simulate Redis success

    response = client.post(
        "/api/v1/users/me/request_disable_2fa",
        json={},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)
    mock_redis_client.return_value.setex.assert_called_once_with(
        f"{SETUP_2FA_REQUEST_PREFIX}:{token_data.ukey}:{ANY}",
        300,
        token_data.email,
    )


# Test Case: Redis error handling
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_request_disable_2fa_redis_error(mock_get_user_by_ukey,
                                         mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_user = MagicMock(spec=User)
    mock_user.mfa_enabled = True  # MFA enabled
    mock_get_user_by_ukey.return_value = mock_user

    mock_redis_client.return_value.setex.side_effect = Exception(
        "Redis error")  # Simulate Redis error

    response = client.post(
        "/api/v1/users/me/request_disable_2fa",
        json={},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 500
    assert "Internal Server Error" in response.text
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)
    mock_redis_client.return_value.setex.assert_called_once_with(
        f"{SETUP_2FA_REQUEST_PREFIX}:{token_data.ukey}:{ANY}",
        300,
        token_data.email,
    )


# Test Case: User not found
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_disable_2fa_user_not_found(mock_get_user_by_ukey, mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_get_user_by_ukey.return_value = None  # User not found

    response = client.patch(
        "/api/v1/users/me/disable_2fa",
        json={"code": "mfa_code"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)


# Test Case: Invalid MFA code
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_disable_2fa_invalid_mfa_code(mock_get_user_by_ukey, mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_user = MagicMock(spec=User)
    mock_user.mfa_enabled = True  # MFA enabled
    mock_get_user_by_ukey.return_value = mock_user

    mock_redis_client.return_value.get.return_value = None  # Invalid or expired MFA code

    response = client.patch(
        "/api/v1/users/me/disable_2fa",
        json={"code": "invalid_mfa_code"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)


# Test Case: User's ukey is None
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_disable_2fa_ukey_none(mock_get_user_by_ukey, mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = None  # ukey is None

    response = client.patch(
        "/api/v1/users/me/disable_2fa",
        json={"code": "mfa_code"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request"
    mock_get_user_by_ukey.assert_not_called()
    mock_redis_client.return_value.get.assert_not_called()


# Test Case: Redis error when retrieving MFA code
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
def test_disable_2fa_redis_error(mock_get_user_by_ukey, mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_user = MagicMock(spec=User)
    mock_user.mfa_enabled = True  # MFA enabled
    mock_get_user_by_ukey.return_value = mock_user

    # Simulate Redis error (e.g., connection failure)
    mock_redis_client.return_value.get.side_effect = Exception("Redis error")

    response = client.patch(
        "/api/v1/users/me/disable_2fa",
        json={"code": "mfa_code"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 500
    assert "Internal Server Error" in response.text
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)
    mock_redis_client.return_value.get.assert_called_once_with(
        f"{SETUP_2FA_REQUEST_PREFIX}:{token_data.ukey}:mfa_code"
    )


# Test Case: Successfully disable MFA
@patch("app.redis_cache.get_redis_client")
@patch("app.db.managers.user_manager.get_user_by_ukey")
@patch("app.db.managers.user_manager.update_user")
def test_disable_2fa_success(mock_update_user, mock_get_user_by_ukey,
                             mock_redis_client):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_user = MagicMock(spec=User)
    mock_user.mfa_enabled = True  # MFA enabled
    mock_get_user_by_ukey.return_value = mock_user

    # Simulate Redis returning a valid MFA code
    mock_redis_client.return_value.get.return_value = b"test_email"

    response = client.patch(
        "/api/v1/users/me/disable_2fa",
        json={"code": "mfa_code"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    assert response.json()["mfa_enabled"] is False
    mock_get_user_by_ukey.assert_called_once_with(ANY, token_data.ukey)
    mock_redis_client.return_value.get.assert_called_once_with(
        f"{SETUP_2FA_REQUEST_PREFIX}:{token_data.ukey}:mfa_code"
    )
    mock_update_user.assert_called_once_with(ANY, mock_user)


# Test Case: User is not found
def test_send_code_for_temp_conversion_user_not_found(mock_get_user_by_email):
    mock_get_user_by_email.return_value = None  # User not found

    user_model = {"email": "testuser@example.com"}
    response = client.post(
        "/api/v1/users/temp/send-verification",
        json=user_model,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"


# Test Case: User is not temporary
def test_send_code_for_temp_conversion_user_not_temporary(
        mock_get_user_by_email):
    mock_user = MagicMock(spec=User)
    mock_user.temporary = False  # User is not temporary
    mock_get_user_by_email.return_value = mock_user

    user_model = {"email": "testuser@example.com"}
    response = client.post(
        "/api/v1/users/temp/send-verification",
        json=user_model,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not temporary"


# Test Case: Redis fails to store the MFA code
@patch("app.redis_cache.get_redis_client")
@patch("app.email_sender.get_email_sender")
@patch("app.db.managers.user_manager.get_user_by_email")
def test_send_code_for_temp_conversion_redis_error(
        mock_get_user_by_email, mock_email_sender, mock_redis_client
):
    mock_user = MagicMock(spec=User)
    mock_user.temporary = True  # User is temporary
    mock_user.email = "testuser@example.com"
    mock_get_user_by_email.return_value = mock_user

    # Simulate Redis error (e.g., connection failure)
    mock_redis_client.return_value.set.side_effect = Exception("Redis error")

    user_model = {"email": "testuser@example.com"}
    response = client.post(
        "/api/v1/users/temp/send-verification",
        json=user_model,
    )

    assert response.status_code == 500
    assert "Internal Server Error" in response.text


# Test Case: Successfully generate MFA code and send email
@patch("app.redis_cache.get_redis_client")
@patch("app.email_sender.get_email_sender")
@patch("app.db.managers.user_manager.get_user_by_email")
def test_send_code_for_temp_conversion_success(
        mock_get_user_by_email, mock_email_sender, mock_redis_client
):
    mock_user = MagicMock(spec=User)
    mock_user.temporary = True  # User is temporary
    mock_user.email = "testuser@example.com"
    mock_get_user_by_email.return_value = mock_user

    mock_redis_client.return_value.set.return_value = None  # Mock Redis set
    mock_email_sender.return_value.send_message.return_value = None  # Mock email send

    user_model = {"email": "testuser@example.com"}
    response = client.post(
        "/api/v1/users/temp/send-verification",
        json=user_model,
    )

    assert response.status_code == 200
    mock_redis_client.return_value.set.assert_called_once()
    mock_email_sender.return_value.send_message.assert_called_once_with(
        subject="Your registration verification code",
        text=ANY,  # Any string containing the code
        to=["testuser@example.com"],
    )


# Test Case: User is not found
def test_get_user_orders_user_not_found(mock_get_user_by_ukey):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"

    mock_get_user_by_ukey.return_value = None  # User not found

    response = client.get(
        "/api/v1/users/me/orders",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User is not found"


# Test Case: User has no orders
def test_get_user_orders_no_orders(mock_get_user_by_ukey,
                                   mock_get_orders_by_user_id):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"
    mock_user = MagicMock(spec=User)
    mock_get_user_by_ukey.return_value = mock_user
    mock_get_orders_by_user_id.return_value = []  # No orders

    response = client.get(
        "/api/v1/users/me/orders",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    assert response.json() == []  # Empty list of orders


# Test Case: User has orders
def test_get_user_orders_with_orders(mock_get_user_by_ukey,
                                     mock_get_orders_by_user_id):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"
    mock_user = MagicMock(spec=User)
    mock_get_user_by_ukey.return_value = mock_user

    mock_order = MagicMock(spec=OrderResponseModel)
    mock_get_orders_by_user_id.return_value = [mock_order]  # User has orders

    response = client.get(
        "/api/v1/users/me/orders",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1  # List contains one order
    assert response.json()[
               0] == mock_order.dict()  # The order data should match


# Test Case: Unauthorized Access
def test_get_user_orders_unauthorized():
    response = client.get(
        "/api/v1/users/me/orders",
        headers={"Authorization": "Bearer unauthorized_token"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


# Test Case: Error in fetching orders
@patch("app.db.managers.orders.get_orders_by_user_id")
def test_get_user_orders_db_error(mock_get_orders_by_user_id,
                                  mock_get_user_by_ukey):
    token_data = MagicMock(spec=TokenData)
    token_data.ukey = "test_ukey"
    mock_user = MagicMock(spec=User)
    mock_get_user_by_ukey.return_value = mock_user

    # Simulate a database error
    mock_get_orders_by_user_id.side_effect = Exception("Database error")

    response = client.get(
        "/api/v1/users/me/orders",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 500
    assert "Internal Server Error" in response.text
