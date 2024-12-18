import pytest
from unittest.mock import AsyncMock
from app.business_logic.stripe import (
    create_payment_intent,
    verify_payment,
    get_receipt_url,
)
from app.business_logic.exceptions import PaymentNotSuccessful, StripePaymentError
from app.dto_schemas.stripe import StripeClientSecret
from app.db.models import Game


@pytest.fixture
def game():
    return Game(id=1, price=19.99)  # Mocking a game with a price


# Test for create_payment_intent
@pytest.mark.asyncio
async def test_create_payment_intent_success(game, mocker):
    # Mocking Stripe's PaymentIntent.create_async method
    mock_create_async = mocker.patch("stripe.PaymentIntent.create_async", new_callable=AsyncMock)
    mock_create_async.return_value = AsyncMock(client_secret="secret123")

    result = await create_payment_intent(game)

    assert isinstance(result, StripeClientSecret)
    assert result.clientSecret == "secret123"
    mock_create_async.assert_called_once_with(
        amount=1999,  # 19.99 * 100 (in cents)
        currency="usd",
        payment_method_types=["card"],
        metadata={"game_id": "1"},
    )


@pytest.mark.asyncio
async def test_create_payment_intent_no_client_secret(game, mocker):
    # Mocking Stripe's PaymentIntent.create_async method to return no client secret
    mock_create_async = mocker.patch("stripe.PaymentIntent.create_async", new_callable=AsyncMock)
    mock_create_async.return_value = AsyncMock(client_secret=None)

    with pytest.raises(StripePaymentError):
        await create_payment_intent(game)
    mock_create_async.assert_called_once()


@pytest.mark.asyncio
async def test_create_payment_intent_stripe_error(game, mocker):
    # Mocking Stripe's PaymentIntent.create_async to raise a StripeError
    mock_create_async = mocker.patch("stripe.PaymentIntent.create_async", new_callable=AsyncMock)
    mock_create_async.side_effect = StripeError("Stripe error")

    with pytest.raises(StripePaymentError):
        await create_payment_intent(game)
    mock_create_async.assert_called_once()


# Test for verify_payment
@pytest.mark.asyncio
async def test_verify_payment_success(mocker):
    # Mocking Stripe's PaymentIntent.retrieve_async method
    mock_retrieve_async = mocker.patch("stripe.PaymentIntent.retrieve_async", new_callable=AsyncMock)
    mock_retrieve_async.return_value = AsyncMock(status="succeeded")

    result = await verify_payment("payment_intent_id")

    assert result.status == "succeeded"
    mock_retrieve_async.assert_called_once_with("payment_intent_id")


@pytest.mark.asyncio
async def test_verify_payment_failed(mocker):
    # Mocking Stripe's PaymentIntent.retrieve_async method
    mock_retrieve_async = mocker.patch("stripe.PaymentIntent.retrieve_async", new_callable=AsyncMock)
    mock_retrieve_async.return_value = AsyncMock(status="failed")

    with pytest.raises(PaymentNotSuccessful):
        await verify_payment("payment_intent_id")
    mock_retrieve_async.assert_called_once_with("payment_intent_id")


@pytest.mark.asyncio
async def test_verify_payment_stripe_error(mocker):
    # Mocking Stripe's PaymentIntent.retrieve_async to raise a StripeError
    mock_retrieve_async = mocker.patch("stripe.PaymentIntent.retrieve_async", new_callable=AsyncMock)
    mock_retrieve_async.side_effect = StripeError("Stripe error")

    with pytest.raises(StripePaymentError):
        await verify_payment("payment_intent_id")
    mock_retrieve_async.assert_called_once_with("payment_intent_id")


# Test for get_receipt_url
@pytest.mark.asyncio
async def test_get_receipt_url_success(mocker):
    # Mocking Stripe's Charge.retrieve_async method
    mock_retrieve_async = mocker.patch("stripe.Charge.retrieve_async", new_callable=AsyncMock)
    mock_retrieve_async.return_value = AsyncMock(receipt_url="https://receipt.url")

    result = await get_receipt_url(AsyncMock(latest_charge="charge_id"))

    assert result == "https://receipt.url"
    mock_retrieve_async.assert_called_once_with("charge_id")


@pytest.mark.asyncio
async def test_get_receipt_url_stripe_error(mocker):
    # Mocking Stripe's Charge.retrieve_async to raise a StripeError
    mock_retrieve_async = mocker.patch("stripe.Charge.retrieve_async", new_callable=AsyncMock)
    mock_retrieve_async.side_effect = StripeError("Stripe error")

    with pytest.raises(StripePaymentError):
        await get_receipt_url(AsyncMock(latest_charge="charge_id"))
    mock_retrieve_async.assert_called_once_with("charge_id")
