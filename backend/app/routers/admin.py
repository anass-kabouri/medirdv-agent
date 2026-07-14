import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth_dependencies import get_current_admin
from app.database import get_db
from app.models import Patient
from app.schemas import AdminStatsOut, AppointmentHistoryOut
from app.services import export_service, scheduling

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/appointments", response_model=list[AppointmentHistoryOut])
def list_all_appointments(
    current_admin: Patient = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    appointments = scheduling.list_all_appointments(db)
    return [AppointmentHistoryOut(**scheduling.to_appointment_history(a)) for a in appointments]


@router.get("/stats", response_model=AdminStatsOut)
def get_stats(
    current_admin: Patient = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return scheduling.get_admin_stats(db)


@router.get("/export/csv")
def export_csv(
    current_admin: Patient = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    csv_content = export_service.appointments_to_csv(db)
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rendezvous_medirdv.csv"},
    )


@router.get("/export/pdf")
def export_pdf(
    current_admin: Patient = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    pdf_bytes = export_service.appointments_to_pdf(db)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=rendezvous_medirdv.pdf"},
    )