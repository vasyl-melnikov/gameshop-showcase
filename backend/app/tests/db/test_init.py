import pytest
from unittest.mock import MagicMock
from app.db import init_models, get_session, engine, async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker


@pytest.mark.asyncio
async def test_init_models(mocker):
    # Mocking engine and the connection used by init_models
    mock_engine = mocker.patch("app.db.create_async_engine", autospec=True)
    mock_connection = MagicMock()
    mock_engine.return_value.begin.return_value.__aenter__.return_value = mock_connection

    # Mocking the drop_all and create_all methods to avoid real database interactions
    mock_connection.run_sync = MagicMock()

    # Run the init_models function
    await init_models()

    # Assert that the connection methods drop and create tables were called
    mock_connection.run_sync.assert_any_call(mock_connection)
    assert mock_connection.run_sync.call_count == 2  # drop_all and create_all


@pytest.mark.asyncio
async def test_get_session(mocker):
    # Mocking async_sessionmaker to avoid real database session creation
    mock_async_session = mocker.patch("app.db.async_session", autospec=True)
    mock_session = MagicMock(spec=AsyncSession)
    mock_async_session.return_value.__aenter__.return_value = mock_session

    # Testing the session creation
    async for session in get_session():
        # Check if the session was created and is of the correct type
        assert isinstance(session, AsyncSession)
        assert session is mock_session

    # Ensure that the session was used properly within the context manager
    mock_async_session.return_value.__aenter__.assert_called_once()
    mock_async_session.return_value.__aexit__.assert_called_once()
