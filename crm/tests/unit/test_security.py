from uuid import uuid4

import pytest

from infrastructure.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    hashed = hash_password("MySecret123!")
    assert hashed != "MySecret123!"
    assert verify_password("MySecret123!", hashed)
    assert not verify_password("WrongPassword", hashed)


def test_create_and_decode_jwt():
    tenant_id = uuid4()
    user_id = uuid4()

    token = create_access_token(tenant_id, user_id, "admin")
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_invalid_token():
    with pytest.raises(Exception):
        decode_access_token("invalid.token.here")
