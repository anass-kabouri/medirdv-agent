from sqlalchemy.orm import Session

from app.models import Patient
from app.services import auth_service, email_service


class EmailAlreadyRegisteredError(Exception):
    pass


class PatientNotFoundError(Exception):
    pass


class InvalidOrExpiredCodeError(Exception):
    pass


class AlreadyVerifiedError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AccountNotVerifiedError(Exception):
    pass


def get_patient_by_email(db: Session, email: str) -> Patient | None:
    return db.query(Patient).filter(Patient.email.ilike(email)).first()


def get_patient_by_id(db: Session, patient_id: int) -> Patient | None:
    return db.query(Patient).filter(Patient.id == patient_id).first()


def register_patient(db: Session, name: str, email: str, password: str) -> Patient:
    existing = get_patient_by_email(db, email)
    if existing is not None:
        raise EmailAlreadyRegisteredError(f"L'email {email} est deja utilise.")

    code = auth_service.generate_verification_code()

    patient = Patient(
        name=name,
        email=email,
        hashed_password=auth_service.hash_password(password),
        is_verified=False,
        verification_code=code,
        verification_code_expires_at=auth_service.verification_code_expiry(),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    subject, body = email_service.build_verification_email(name, code)
    email_service.send_email(email, subject, body)

    return patient


def verify_patient_email(db: Session, email: str, code: str) -> Patient:
    patient = get_patient_by_email(db, email)
    if patient is None:
        raise PatientNotFoundError(f"Aucun compte trouve pour {email}.")

    if patient.is_verified:
        raise AlreadyVerifiedError("Ce compte est deja verifie.")

    if patient.verification_code != code or auth_service.is_code_expired(
        patient.verification_code_expires_at
    ):
        raise InvalidOrExpiredCodeError("Code invalide ou expire.")

    patient.is_verified = True
    patient.verification_code = None
    patient.verification_code_expires_at = None
    db.commit()
    db.refresh(patient)

    return patient


def resend_verification_code(db: Session, email: str) -> Patient:
    patient = get_patient_by_email(db, email)
    if patient is None:
        raise PatientNotFoundError(f"Aucun compte trouve pour {email}.")

    if patient.is_verified:
        raise AlreadyVerifiedError("Ce compte est deja verifie.")

    code = auth_service.generate_verification_code()
    patient.verification_code = code
    patient.verification_code_expires_at = auth_service.verification_code_expiry()
    db.commit()
    db.refresh(patient)

    subject, body = email_service.build_verification_email(patient.name, code)
    email_service.send_email(email, subject, body)

    return patient


def authenticate_patient(db: Session, email: str, password: str) -> Patient:
    patient = get_patient_by_email(db, email)
    if patient is None or not auth_service.verify_password(password, patient.hashed_password):
        raise InvalidCredentialsError("Email ou mot de passe incorrect.")

    if not patient.is_verified:
        raise AccountNotVerifiedError("Compte non verifie. Verifiez votre email d'abord.")

    return patient