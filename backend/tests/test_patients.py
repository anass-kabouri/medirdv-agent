import pytest

from app.services import patients


def test_register_patient_creates_unverified_account(db_session):
    patient = patients.register_patient(db_session, "Jean Dupont", "jean@example.com", "motdepasse123")

    assert patient.id is not None
    assert patient.is_verified is False
    assert patient.verification_code is not None
    assert len(patient.verification_code) == 6


def test_register_patient_duplicate_email_raises(db_session):
    patients.register_patient(db_session, "Jean Dupont", "jean@example.com", "motdepasse123")

    with pytest.raises(patients.EmailAlreadyRegisteredError):
        patients.register_patient(db_session, "Autre Jean", "jean@example.com", "autremotdepasse")


def test_verify_patient_email_with_correct_code(db_session):
    patient = patients.register_patient(db_session, "Jean Dupont", "jean@example.com", "motdepasse123")
    code = patient.verification_code

    verified = patients.verify_patient_email(db_session, "jean@example.com", code)

    assert verified.is_verified is True
    assert verified.verification_code is None


def test_verify_patient_email_with_wrong_code_raises(db_session):
    patients.register_patient(db_session, "Jean Dupont", "jean@example.com", "motdepasse123")

    with pytest.raises(patients.InvalidOrExpiredCodeError):
        patients.verify_patient_email(db_session, "jean@example.com", "000000")


def test_verify_patient_email_unknown_email_raises(db_session):
    with pytest.raises(patients.PatientNotFoundError):
        patients.verify_patient_email(db_session, "inconnu@example.com", "123456")


def test_verify_already_verified_account_raises(db_session):
    patient = patients.register_patient(db_session, "Jean Dupont", "jean@example.com", "motdepasse123")
    patients.verify_patient_email(db_session, "jean@example.com", patient.verification_code)

    with pytest.raises(patients.AlreadyVerifiedError):
        patients.verify_patient_email(db_session, "jean@example.com", "000000")


def test_resend_verification_code_generates_new_code(db_session):
    patient = patients.register_patient(db_session, "Jean Dupont", "jean@example.com", "motdepasse123")

    updated = patients.resend_verification_code(db_session, "jean@example.com")

    assert updated.verification_code is not None
    assert updated.is_verified is False


def test_authenticate_patient_success_after_verification(db_session):
    patient = patients.register_patient(db_session, "Jean Dupont", "jean@example.com", "motdepasse123")
    patients.verify_patient_email(db_session, "jean@example.com", patient.verification_code)

    authenticated = patients.authenticate_patient(db_session, "jean@example.com", "motdepasse123")
    assert authenticated.email == "jean@example.com"


def test_authenticate_patient_wrong_password_raises(db_session):
    patient = patients.register_patient(db_session, "Jean Dupont", "jean@example.com", "motdepasse123")
    patients.verify_patient_email(db_session, "jean@example.com", patient.verification_code)

    with pytest.raises(patients.InvalidCredentialsError):
        patients.authenticate_patient(db_session, "jean@example.com", "mauvais_mdp")


def test_authenticate_patient_unverified_account_raises(db_session):
    patients.register_patient(db_session, "Jean Dupont", "jean@example.com", "motdepasse123")

    with pytest.raises(patients.AccountNotVerifiedError):
        patients.authenticate_patient(db_session, "jean@example.com", "motdepasse123")


def test_authenticate_patient_unknown_email_raises(db_session):
    with pytest.raises(patients.InvalidCredentialsError):
        patients.authenticate_patient(db_session, "inconnu@example.com", "motdepasse123")