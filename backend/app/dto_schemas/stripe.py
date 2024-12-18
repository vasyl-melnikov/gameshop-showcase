from pydantic import BaseModel


class StripeClientSecret(BaseModel):
    clientSecret: str
