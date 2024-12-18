import random
import string
from typing import AsyncIterator

alphabet = string.ascii_uppercase + string.digits


def generate_ukey() -> str:
    return generate_string(12)


def generate_string(length: int) -> str:
    return "".join(random.choices(alphabet, k=length))


def generate_random_mfa_code() -> str:
    return "".join(random.choices(string.digits, k=6))


async def async_islice(iterable: AsyncIterator, n: int):  # bo mogu, i 4o>????
    count = 0
    async for item in iterable:
        if count >= n:
            break
        yield item
        count += 1
