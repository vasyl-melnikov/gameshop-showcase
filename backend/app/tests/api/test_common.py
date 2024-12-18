import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException, Request
from unittest.mock import patch, MagicMock
from app.main import app
from app.api.common import AuthorizedRequest, get_token_data, get_logger, \
    generate_common_redis_key, get_id_from_common_redis_key
from app.dto_schemas.auth import Roles, TokenData
from app.business_logic.auth import verify_token_access
from app.logger import logger

client = TestClient(app)


# Test for AuthorizedRequest - Success case
@pytest.mark.asyncio
async def test_authorized_request_success():
    # Mock dependencies
    mock_verify_token_access = MagicMock(
        return_value=TokenData(ukey="test_ukey", email="test@example.com",
                               role=Roles.ADMIN))

    # Patch the verify_token_access function
    with patch("app.api.common.verify_token_access", mock_verify_token_access):
        # Create an instance of AuthorizedRequest
        authorized_request = AuthorizedRequest(role=Roles.ADMIN)

        # Simulate a request
        class MockRequest:
            def __init__(self, token):
                self.headers = {"Authorization": f"Bearer {token}"}

        request = MockRequest(token="valid_token")

        # Call the AuthorizedRequest class to verify if it works as expected
        await authorized_request(request)

        # Ensure the token was verified correctly
        mock_verify_token_access.assert_called_once_with("valid_token",
                                                         role=Roles.ADMIN,
                                                         exact_role=False)


# Test for AuthorizedRequest - Invalid token
@pytest.mark.asyncio
async def test_authorized_request_invalid_token():
    # Mock dependencies
    mock_verify_token_access = MagicMock(
        side_effect=HTTPException(status_code=401, detail="Invalid token"))

    # Patch the verify_token_access function
    with patch("app.api.common.verify_token_access", mock_verify_token_access):
        # Create an instance of AuthorizedRequest
        authorized_request = AuthorizedRequest(role=Roles.ADMIN)

        # Simulate a request
        class MockRequest:
            def __init__(self, token):
                self.headers = {"Authorization": f"Bearer {token}"}

        request = MockRequest(token="invalid_token")

        # Expect HTTPException to be raised
        with pytest.raises(HTTPException):
            await authorized_request(request)


# Test for get_token_data
@pytest.mark.asyncio
async def test_get_token_data():
    # Mock request and token data
    class MockRequest:
        def __init__(self, token_data):
            self.token_data = token_data

    token_data = TokenData(ukey="test_ukey", email="test@example.com",
                           role=Roles.USER)
    request = MockRequest(token_data=token_data)

    # Test the get_token_data function
    token_data_result = await get_token_data(request)

    assert token_data_result.ukey == "test_ukey"
    assert token_data_result.email == "test@example.com"
    assert token_data_result.role == Roles.USER


# Test for get_logger
@pytest.mark.asyncio
async def test_get_logger():
    # Mock request and logger
    class MockRequest:
        def __init__(self, client_ip, url_path, method):
            self.client = MagicMock(host=client_ip)
            self.url = MagicMock(path=url_path)
            self.method = method
            self.req_id = "test_request_id"

    request = MockRequest(client_ip="127.0.0.1", url_path="/test", method="GET")

    # Test the get_logger function
    log_context = await get_logger(request)

    # Ensure that the logger context has been set properly
    assert log_context.context["client_ip"] == "127.0.0.1"
    assert log_context.context["path"] == "/test"
    assert log_context.context["method"] == "GET"
    assert log_context.context["req_id"] == "test_request_id"


# Test for generate_common_redis_key
def test_generate_common_redis_key():
    # Test the key generation with known values
    prefix = "test_prefix"
    identifier = "test_identifier"
    expected_key = "test_prefix:test_identifier"

    generated_key = generate_common_redis_key(prefix, identifier)

    # Ensure the generated key matches the expected value
    assert generated_key == expected_key


# Test for get_id_from_common_redis_key
def test_get_id_from_common_redis_key():
    # Test the extraction of ID from the Redis key
    redis_key = b"test_prefix:test_identifier"

    # Ensure the ID is extracted correctly
    extracted_id = get_id_from_common_redis_key(redis_key)

    assert extracted_id == "test_identifier"
