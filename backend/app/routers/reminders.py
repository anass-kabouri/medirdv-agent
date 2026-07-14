from fastapi import APIRouter

from app.services.reminders import send_due_reminders

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("/run")
def run_reminders_now():
    count = send_due_reminders()
    return {"reminders_sent": count}