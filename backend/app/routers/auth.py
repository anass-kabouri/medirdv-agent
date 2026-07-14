from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth_dependencies import get_current_patient
from app.database import get_db
from app.models import Patient
from app.schemas import (
    LoginRequest,
    PatientOut,
    PatientRegister,
    ResendCodeRequest,
    TokenResponse,
    VerifyCodeRequest,
)
from app.services import auth_service, patients

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=PatientOut, status_code=201)
def register(payload: PatientRegister, db: Session = Depends(get_db)):
    try:
        return patients.register_patient(db, payload.name, payload.email, payload.password)
    except patients.EmailAlreadyRegisteredError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/verify", response_model=PatientOut)
def verify(payload: VerifyCodeRequest, db: Session = Depends(get_db)):
    try:
        return patients.verify_patient_email(db, payload.email, payload.code)
    except patients.PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except patients.AlreadyVerifiedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except patients.InvalidOrExpiredCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/resend-code", response_model=PatientOut)
def resend_code(payload: ResendCodeRequest, db: Session = Depends(get_db)):
    try:
        return patients.resend_verification_code(db, payload.email)
    except patients.PatientNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except patients.AlreadyVerifiedError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        patient = patients.authenticate_patient(db, payload.email, payload.password)
    except patients.InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except patients.AccountNotVerifiedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    token = auth_service.create_access_token(patient.id, patient.is_admin)
    return TokenResponse(access_token=token, patient=patient)


@router.get("/me", response_model=PatientOut)
def me(current_patient: Patient = Depends(get_current_patient)):
    return current_patient