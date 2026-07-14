from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient
from app.services import auth_service, patients

security_scheme = HTTPBearer()


def get_current_patient(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Patient:
    token = credentials.credentials
    payload = auth_service.decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token invalide ou expire.")

    patient = patients.get_patient_by_id(db, int(payload["sub"]))
    if patient is None:
        raise HTTPException(status_code=401, detail="Compte introuvable.")

    return patient


def get_current_admin(current_patient: Patient = Depends(get_current_patient)) -> Patient:
    if not current_patient.is_admin:
        raise HTTPException(status_code=403, detail="Acces reserve aux administrateurs.")
    return current_patient