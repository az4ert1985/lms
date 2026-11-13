from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing() -> None:
    password = "Strong-Test-Password-123!"  # noqa: S105

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_token() -> None:
    token = create_access_token("test-user-id")

    payload = decode_access_token(token)

    assert payload["sub"] == "test-user-id"
    assert "exp" in payload
