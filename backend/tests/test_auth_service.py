from datetime import datetime, timedelta, timezone

from app.services import auth_service


def test_hash_and_verify_password():
    hashed = auth_service.hash_password("motdepasse123")
    assert hashed != "motdepasse123"
    assert auth_service.verify_password("motdepasse123", hashed) is True
    assert auth_service.verify_password("mauvais_mot_de_passe", hashed) is False


def test_generate_verification_code_is_six_digits():
    code = auth_service.generate_verification_code()
    assert len(code) == 6
    assert code.isdigit()


def test_verification_code_expiry_is_in_the_future():
    expiry = auth_service.verification_code_expiry()
    assert expiry > datetime.now(timezone.utc)


def test_is_code_expired_detects_past_date():
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    assert auth_service.is_code_expired(past) is True


def test_is_code_expired_detects_future_date():
    future = datetime.now(timezone.utc) + timedelta(minutes=10)
    assert auth_service.is_code_expired(future) is False


def test_is_code_expired_none_is_expired():
    assert auth_service.is_code_expired(None) is True


def test_create_and_decode_access_token():
    token = auth_service.create_access_token(patient_id=42, is_admin=False)
    payload = auth_service.decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["is_admin"] is False


def test_decode_invalid_token_returns_none():
    assert auth_service.decode_access_token("token.invalide.ici") is None