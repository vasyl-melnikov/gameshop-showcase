import pytest
from unittest.mock import MagicMock

from app.db.managers.exceptions import UserNotFound
from app.db.managers.user_manager import (
    get_user_by_id,
    get_users,
    add_user,
    add_temp_user,
    update_user,
    get_user_by_email,
    get_user_by_ukey,
    update_role_by_email,
    update_password_by_id
)
from app.db.models import User
from app.dto_schemas.auth import Roles
from app.dto_schemas.user import UserCreate, EmailOnlyUser


@pytest.fixture
def mock_db_session(mocker):
    return mocker.MagicMock()


@pytest.fixture
def user_data():
    return User(
        id=1,
        ukey="unique-key-123",
        email="test@example.com",
        username="testuser",
        role=Roles.USER,
        first_name="Test",
        last_name="User",
        hashed_password="hashedpassword"
    )


# Test for get_user_by_id
@pytest.mark.asyncio
async def test_get_user_by_id(mock_db_session, user_data, mocker):
    # Mock the query result
    mock_db_session.scalars.return_value.first.return_value = user_data

    result = await get_user_by_id(mock_db_session, 1)

    assert result == user_data
    mock_db_session.scalars.assert_called_once()


# Test for get_users
@pytest.mark.asyncio
async def test_get_users(mock_db_session, user_data):
    # Mock the query result
    mock_db_session.scalars.return_value.all.return_value = [user_data]

    result = await get_users(mock_db_session)

    assert len(result) == 1
    assert result[0] == user_data
    mock_db_session.scalars.assert_called_once()


# Test for add_user
@pytest.mark.asyncio
async def test_add_user(mock_db_session, mocker):
    # Mock the commit and add methods
    mock_db_session.commit = MagicMock()
    mock_db_session.add = MagicMock()

    user_create_model = UserCreate(
        username="newuser",
        first_name="New",
        last_name="User",
        email="newuser@example.com",
        password="password123"
    )

    result = await add_user(mock_db_session, user_create_model)

    assert isinstance(result, User)
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


# Test for add_temp_user
@pytest.mark.asyncio
async def test_add_temp_user(mock_db_session, mocker):
    # Mock the commit and add methods
    mock_db_session.commit = MagicMock()
    mock_db_session.add = MagicMock()

    temp_user_create_model = EmailOnlyUser(email="tempuser@example.com")

    result = await add_temp_user(mock_db_session, temp_user_create_model)

    assert isinstance(result, User)
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


# Test for update_user
@pytest.mark.asyncio
async def test_update_user(mock_db_session, user_data, mocker):
    # Mock the commit and add methods
    mock_db_session.commit = MagicMock()
    mock_db_session.add = MagicMock()

    user_data.first_name = "Updated"

    result = await update_user(mock_db_session, user_data)

    assert result.first_name == "Updated"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


# Test for get_user_by_email
@pytest.mark.asyncio
async def test_get_user_by_email(mock_db_session, user_data):
    # Mock the query result
    mock_db_session.scalars.return_value.first.return_value = user_data

    result = await get_user_by_email(mock_db_session, "test@example.com")

    assert result == user_data
    mock_db_session.scalars.assert_called_once()


# Test for get_user_by_ukey
@pytest.mark.asyncio
async def test_get_user_by_ukey(mock_db_session, user_data):
    # Mock the query result
    mock_db_session.scalars.return_value.first.return_value = user_data

    result = await get_user_by_ukey(mock_db_session, "unique-key-123")

    assert result == user_data
    mock_db_session.scalars.assert_called_once()


# Test for update_role_by_email (User exists)
@pytest.mark.asyncio
async def test_update_role_by_email(mock_db_session, user_data):
    # Mock the query result
    mock_db_session.scalars.return_value.first.return_value = user_data
    mock_db_session.commit = MagicMock()

    result = await update_role_by_email(mock_db_session, "test@example.com", Roles.ADMIN)

    assert result.role == Roles.ADMIN
    mock_db_session.commit.assert_called_once()


# Test for update_role_by_email (User not found)
@pytest.mark.asyncio
async def test_update_role_by_email_user_not_found(mock_db_session):
    # Mock the query result
    mock_db_session.scalars.return_value.first.return_value = None

    with pytest.raises(UserNotFound):
        await update_role_by_email(mock_db_session, "nonexistent@example.com", Roles.ADMIN)


# Test for update_password_by_id (User exists)
@pytest.mark.asyncio
async def test_update_password_by_id(mock_db_session, user_data):
    # Mock the query result
    mock_db_session.scalars.return_value.first.return_value = user_data
    mock_db_session.commit = MagicMock()

    result = await update_password_by_id(mock_db_session, "1", "newpassword123")

    assert result.hashed_password == "newpassword123"
    mock_db_session.commit.assert_called_once()


# Test for update_password_by_id (User not found)
@pytest.mark.asyncio
async def test_update_password_by_id_user_not_found(mock_db_session):
    # Mock the query result
    mock_db_session.scalars.return_value.first.return_value = None

    with pytest.raises(UserNotFound):
        await update_password_by_id(mock_db_session, "1", "newpassword123")
