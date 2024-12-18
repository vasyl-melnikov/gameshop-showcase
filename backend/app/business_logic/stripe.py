import stripe
from stripe import PaymentIntent, StripeError

from app.business_logic.exceptions import (PaymentNotSuccessful,
                                           StripePaymentError)
from app.db.models import Game
from app.dto_schemas.stripe import StripeClientSecret
from app.settings import settings

stripe.api_key = settings.stripe.secret_key


async def create_payment_intent(game: Game) -> StripeClientSecret:
    try:
        intent = await stripe.PaymentIntent.create_async(
            amount=int(game.price * 100),  # Price in cents
            currency="usd",
            payment_method_types=["card"],
            metadata={"game_id": str(game.id)},
        )

        if intent.client_secret:
            return StripeClientSecret(clientSecret=intent.client_secret)
        else:
            raise StripePaymentError()

    except StripeError as e:
        raise StripePaymentError() from e


async def verify_payment(payment_intend_id: str) -> PaymentIntent:
    try:
        payment_intent = await stripe.PaymentIntent.retrieve_async(payment_intend_id)

        if payment_intent.status == "succeeded":
            return payment_intent
        else:
            raise PaymentNotSuccessful()
    except StripeError as e:
        raise StripePaymentError() from e


async def get_receipt_url(payment_intent: PaymentIntent) -> str | None:
    charge_id = payment_intent.latest_charge
    charge = await stripe.Charge.retrieve_async(str(charge_id))
    return charge.receipt_url
