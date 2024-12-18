import time
import pytest
from unittest.mock import patch
from jose import JWTError
from app.business_logic.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_mfa_only_access_token,
    resolve_exact_role_access,
    resolve_role_access,
    verify_token_access,
    SECRET_KEY,
    ALGORITHM,
)
from app.business_logic.exceptions import AuthorizationError, \
    AuthenticationError
from app.dto_schemas.auth import Roles
from app.dto_schemas.auth import TokenData


# Test for hash_password and verify_password functions
@pytest.fixture
def password():
    return "securePassword123"


def test_hash_password(password):
    hashed_password = hash_password(password)
    assert hashed_password != password  # Ensure the password is hashed
    assert verify_password(password,
                           hashed_password)  # Ensure the password matches


# Test for create_access_token
@pytest.fixture
def valid_user_data():
    return {
        "ukey": "user-123",
        "email": "user@example.com",
        "role": Roles.USER,
    }


def test_create_access_token(valid_user_data):
    token = create_access_token(
        valid_user_data["ukey"], valid_user_data["email"],
        valid_user_data["role"]
    )
    assert isinstance(token, str)  # Ensure the token is a string
    assert len(token) > 0  # Ensure the token is not empty


# Test for create_mfa_only_access_token
def test_create_mfa_only_access_token(valid_user_data):
    token = create_mfa_only_access_token(valid_user_data["ukey"],
                                         valid_user_data["email"])
    assert isinstance(token, str)  # Ensure the token is a string
    assert len(token) > 0  # Ensure the token is not empty


# Test for resolve_exact_role_access
def test_resolve_exact_role_access():
    resolve_exact_role_access(Roles.ADMIN,
                              Roles.ADMIN)  # No exception should be raised
    with pytest.raises(AuthorizationError):
        resolve_exact_role_access(Roles.USER, Roles.ADMIN)


# Test for resolve_role_access
def test_resolve_role_access():
    resolve_role_access(Roles.ADMIN,
                        Roles.USER)  # No exception should be raised
    resolve_role_access(Roles.ADMIN,
                        Roles.SUPPORT_MODERATOR)  # No exception should be raised

    with pytest.raises(AuthorizationError):
        resolve_role_access(Roles.USER, Roles.ADMIN, strict=True)


# Test for verify_token_access with a valid token
@patch("app.business_logic.auth.jwt.decode")
def test_verify_token_access_valid(mock_decode, valid_user_data):
    mock_decode.return_value = {
        "ukey": valid_user_data["ukey"],
        "email": valid_user_data["email"],
        "role": valid_user_data["role"],
        "exp": int(time.time()) + 3600,  # 1 hour from now
    }

    token = create_access_token(
        valid_user_data["ukey"], valid_user_data["email"],
        valid_user_data["role"]
    )
    token_data = verify_token_access(token, Roles.USER)

    assert isinstance(token_data, TokenData)
    assert token_data.ukey == valid_user_data["ukey"]
    assert token_data.email == valid_user_data["email"]
    assert token_data.role == valid_user_data["role"]


# Test for verify_token_access with an invalid token
@patch("app.business_logic.auth.jwt.decode")
def test_verify_token_access_invalid(mock_decode):
    mock_decode.side_effect = JWTError  # Simulate a decoding error

    with pytest.raises(AuthenticationError):
        verify_token_access("invalid_token", Roles.USER)
