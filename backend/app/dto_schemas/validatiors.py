import re
from typing import Annotated

from pydantic import AfterValidator, PlainSerializer, WithJsonSchema


def validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", value):
        raise ValueError("Password must contain at least one digit.")
    return value


Password = Annotated[
    str,
    AfterValidator(validate_password),
    PlainSerializer(lambda value: value, return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]
