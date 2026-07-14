from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Appointment, AppointmentStatus, Slot
from app.services import email_service


def send_due_reminders() -> int:
    db = SessionLocal()
    try:
        now = datetime.now()
        window_end = now + timedelta(hours=24)

        appointments = (
            db.query(Appointment)
            .join(Slot, Appointment.slot_id == Slot.id)
            .filter(
                Appointment.status == AppointmentStatus.confirmed,
                Appointment.reminder_sent.is_(False),
                Slot.start_time >= now,
                Slot.start_time <= window_end,
            )
            .all()
        )

        for appointment in appointments:
            subject, body = email_service.build_reminder_email(
                patient_name=appointment.patient_name,
                practitioner_name=appointment.slot.practitioner.name,
                specialty=appointment.slot.practitioner.specialty,
                start_time=appointment.slot.start_time,
            )
            email_service.send_email(appointment.patient_email, subject, body)
            appointment.reminder_sent = True

        db.commit()

        if appointments:
            print(f"{len(appointments)} rappel(s) envoye(s).")

        return len(appointments)
    finally:
        db.close()