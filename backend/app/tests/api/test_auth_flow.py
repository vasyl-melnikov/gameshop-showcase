import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app  # FastAPI app instance
from app.dto_schemas.auth import Token, TokenType, Roles
from app.dto_schemas.user import UserCreate, UserLogin, EmailOnlyUser
from app.db.models import User
from app.business_logic.auth import verify_password
from app.db.managers.exceptions import UserNotFound
from app.business_logic.auth import create_access_token

# Set up the TestClient for FastAPI
client = TestClient(app)


@pytest.mark.asyncio
async def test_login_success():
    # Mock the dependencies
    mock_get_user_by_email = MagicMock(
        return_value=User(id=1, email="test@example.com",
                          hashed_password="hashed_password", mfa_enabled=True))
    mock_verify_password = MagicMock(return_value=True)
    mock_generate_random_mfa_code = MagicMock(return_value="123456")
    mock_redis_set = MagicMock()

    # Patch the dependencies
    with patch("app.api.auth_flow.get_user_by_email", mock_get_user_by_email), \
            patch("app.api.auth_flow.verify_password", mock_verify_password), \
            patch("app.api.auth_flow.generate_random_mfa_code",
                  mock_generate_random_mfa_code), \
            patch("app.api.auth_flow.get_redis_client",
                  MagicMock(setex=mock_redis_set)):
        # Create a valid UserLogin request body
        user_login = UserLogin(email="test@example.com", password="password")

        # Send the POST request to login
        response = client.post("/login", json=user_login.dict())

        # Ensure the response is as expected
        assert response.status_code == 200
        assert response.json()["token_type"] == TokenType.BEARER
        assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    # Mock the dependencies to simulate invalid credentials
    mock_get_user_by_email = MagicMock(return_value=None)

    # Patch the dependencies
    with patch("app.api.auth_flow.get_user_by_email", mock_get_user_by_email):
        # Create a valid UserLogin request body
        user_login = UserLogin(email="invalid@example.com",
                               password="wrongpassword")

        # Send the POST request to login
        response = client.post("/login", json=user_login.dict())

        # Ensure the response is a 400 error due to invalid credentials
        assert response.status_code == 400
        assert response.json()["detail"] == "User email or password is invalid"


@pytest.mark.asyncio
async def test_authenticate_mfa_success():
    # Mock the dependencies
    mock_get_user_by_ukey = MagicMock(
        return_value=User(id=1, ukey="user_ukey", email="test@example.com",
                          mfa_enabled=True))
    mock_redis_get = MagicMock(return_value="123456")
    mock_create_access_token = MagicMock(return_value="new_access_token")

    # Patch the dependencies
    with patch("app.api.auth_flow.get_user_by_ukey", mock_get_user_by_ukey), \
            patch("app.api.auth_flow.get_redis_client",
                  MagicMock(get=mock_redis_get)), \
            patch("app.api.auth_flow.create_access_token",
                  mock_create_access_token):
        # Create a valid MFACode request body
        mfa_code = {"code": "123456"}

        # Send the POST request to authenticate with MFA
        response = client.post("/login/auth", json=mfa_code,
                               headers={"Authorization": "Bearer test_token"})

        # Ensure the response is as expected
        assert response.status_code == 200
        assert response.json()["token_type"] == TokenType.BEARER
        assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_authenticate_mfa_invalid_code():
    # Mock the dependencies
    mock_get_user_by_ukey = MagicMock(
        return_value=User(id=1, ukey="user_ukey", email="test@example.com",
                          mfa_enabled=True))
    mock_redis_get = MagicMock(return_value="123456")

    # Patch the dependencies
    with patch("app.api.auth_flow.get_user_by_ukey", mock_get_user_by_ukey), \
            patch("app.api.auth_flow.get_redis_client",
                  MagicMock(get=mock_redis_get)):
        # Create an invalid MFACode request body
        mfa_code = {"code": "654321"}

        # Send the POST request to authenticate with MFA
        response = client.post("/login/auth", json=mfa_code,
                               headers={"Authorization": "Bearer test_token"})

        # Ensure the response is a 403 error due to invalid MFA code
        assert response.status_code == 403
        assert response.json()["detail"] == "Invalid authorization code."


@pytest.mark.asyncio
async def test_register_success():
    # Mock the dependencies
    mock_get_user_by_email = MagicMock(return_value=None)
    mock_add_user = MagicMock(return_value=User(id=1, email="test@example.com",
                                                hashed_password="hashed_password",
                                                role=Roles.USER))

    # Patch the dependencies
    with patch("app.api.auth_flow.get_user_by_email", mock_get_user_by_email), \
            patch("app.api.auth_flow.add_user", mock_add_user):
        # Create a valid UserCreate request body
        user_create = UserCreate(email="test@example.com", password="password",
                                 username="testuser")

        # Send the POST request to register the user
        response = client.post("/register", json=user_create.dict())

        # Ensure the response is as expected
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
        assert "ukey" in response.json()


@pytest.mark.asyncio
async def test_register_user_exists():
    # Mock the dependencies to simulate existing user
    mock_get_user_by_email = MagicMock(
        return_value=User(id=1, email="test@example.com",
                          hashed_password="hashed_password", role=Roles.USER))

    # Patch the dependencies
    with patch("app.api.auth_flow.get_user_by_email", mock_get_user_by_email):
        # Create a valid UserCreate request body
        user_create = UserCreate(email="test@example.com", password="password",
                                 username="testuser")

        # Send the POST request to register the user
        response = client.post("/register", json=user_create.dict())

        # Ensure the response is a 400 error due to the user already existing
        assert response.status_code == 400
        assert response.json()[
                   "detail"] == "User with such email address already exist"


@pytest.mark.asyncio
async def test_register_temp_success():
    # Mock the dependencies
    mock_get_user_by_email = MagicMock(return_value=None)
    mock_add_temp_user = MagicMock(
        return_value=User(id=1, email="temp@example.com", role=Roles.USER))

    # Patch the dependencies
    with patch("app.api.auth_flow.get_user_by_email", mock_get_user_by_email), \
            patch("app.api.auth_flow.add_temp_user", mock_add_temp_user):
        # Create a valid EmailOnlyUser request body
        temp_user_create = EmailOnlyUser(email="temp@example.com")

        # Send the POST request to register a temporary user
        response = client.post("/register/temporary",
                               json=temp_user_create.dict())

        # Ensure the response is as expected
        assert response.status_code == 200
        assert response.json()["email"] == "temp@example.com"
        assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_register_temp_user_exists():
    # Mock the dependencies to simulate existing user
    mock_get_user_by_email = MagicMock(
        return_value=User(id=1, email="temp@example.com", role=Roles.USER))

    # Patch the dependencies
    with patch("app.api.auth_flow.get_user_by_email", mock_get_user_by_email):
        # Create a valid EmailOnlyUser request body
        temp_user_create = EmailOnlyUser(email="temp@example.com")

        # Send the POST request to register a temporary user
        response = client.post("/register/temporary",
                               json=temp_user_create.dict())

        # Ensure the response is a 400 error due to the user already existing
        assert response.status_code == 400
        assert response.json()[
                   "detail"] == "User with such email address already exist"
