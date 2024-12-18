import pytest
from unittest.mock import MagicMock, AsyncMock
from app.utils import generate_ukey, generate_string, generate_random_mfa_code, async_islice


# Test for generate_ukey
def test_generate_ukey():
    # Since generate_ukey simply calls generate_string with length 12,
    # we can directly test it by checking the length of the generated string
    ukey = generate_ukey()
    assert len(ukey) == 12  # Ensure the key is of length 12
    assert ukey.isalnum()  # Ensure the key contains only alphanumeric characters


# Test for generate_string
def test_generate_string():
    # Test that generate_string generates a string of the given length
    length = 10
    random_string = generate_string(length)
    assert len(random_string) == length  # Ensure correct length
    assert random_string.isalnum()  # Ensure it contains only alphanumeric characters

    # Test with different lengths
    random_string_5 = generate_string(5)
    assert len(random_string_5) == 5

    random_string_20 = generate_string(20)
    assert len(random_string_20) == 20


# Test for generate_random_mfa_code
def test_generate_random_mfa_code():
    mfa_code = generate_random_mfa_code()
    assert len(mfa_code) == 6  # Ensure the MFA code is of length 6
    assert mfa_code.isdigit()  # Ensure the code is numeric


# Test for async_islice
@pytest.mark.asyncio
async def test_async_islice():
    # Create an async generator
    async def async_gen():
        for i in range(10):
            yield i

    # Slice the async generator to get only the first 3 elements
    async_iterator = async_gen()
    sliced = [item async for item in async_islice(async_iterator, 3)]

    assert sliced == [0, 1, 2]  # Ensure it slices correctly
    # Ensure the generator is fully exhausted
    async for item in async_islice(async_gen(), 0):
        assert False, "Iterator should be exhausted"
