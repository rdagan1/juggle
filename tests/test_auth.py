"""Unit tests for auth service functions (no DB required)."""
import pytest
from app.services.auth import (
    check_verification_code,
    generate_verification_code,
    generate_virtual_email,
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
import uuid


def test_password_hash_and_verify():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_verification_code_flow():
    email = "test@example.com"
    code = generate_verification_code(email)
    assert len(code) == 6
    assert code.isdigit()

    assert not check_verification_code(email, "000000")
    assert check_verification_code(email, code)
    # Code is consumed after use
    assert not check_verification_code(email, code)


def test_jwt_roundtrip():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)


def test_virtual_email_format():
    ve = generate_virtual_email("Dana Cohen")
    parts = ve.split("@")
    assert parts[1] == "students.juggle.app"
    local_parts = parts[0].split(".")
    assert local_parts[0] == "dana"
    assert local_parts[1] == "cohen"
    assert len(local_parts[2]) == 4


def test_virtual_email_single_name():
    ve = generate_virtual_email("Moshe")
    assert ve.endswith("@students.juggle.app")


def test_virtual_email_no_name():
    ve = generate_virtual_email(None)
    assert ve.endswith("@students.juggle.app")
