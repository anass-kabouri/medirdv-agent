from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth_dependencies import get_current_patient
from app.database import get_db
from app.models import Patient
from app.schemas import AppointmentCreate, AppointmentHistoryOut, AppointmentOut
from app.services import scheduling

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("/history", response_model=list[AppointmentHistoryOut])
def get_appointment_history(
    email: str = Query(..., description="Email du patient"),
    db: Session = Depends(get_db),
):
    appointments = scheduling.get_appointments_by_email(db, email)
    return [AppointmentHistoryOut(**scheduling.to_appointment_history(a)) for a in appointments]


@router.get("/me", response_model=list[AppointmentHistoryOut])
def get_my_appointments(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    appointments = scheduling.get_appointments_by_email(db, current_patient.email)
    return [AppointmentHistoryOut(**scheduling.to_appointment_history(a)) for a in appointments]


@router.post("/", response_model=AppointmentOut, status_code=201)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    try:
        return scheduling.book_slot(
            db, payload.slot_id, payload.patient_name, payload.patient_email
        )
    except scheduling.SlotNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except scheduling.SlotAlreadyBookedError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = scheduling.get_appointment(db, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")
    return appointment


@router.delete("/{appointment_id}", response_model=AppointmentOut)
def delete_appointment(
    appointment_id: int,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    appointment = scheduling.get_appointment(db, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")

    is_owner = appointment.patient_email.lower() == current_patient.email.lower()
    if not current_patient.is_admin and not is_owner:
        raise HTTPException(
            status_code=403, detail="Vous ne pouvez annuler que vos propres rendez-vous."
        )

    try:
        return scheduling.cancel_appointment(db, appointment_id)
    except scheduling.AppointmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))