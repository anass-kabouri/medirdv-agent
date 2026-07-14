from datetime import datetime, timedelta

from sqlalchemy import func as sql_func
from sqlalchemy.orm import Session

from app.models import Appointment, AppointmentStatus, Practitioner, Slot
from app.services import email_service


class SlotNotFoundError(Exception):
    pass


class SlotAlreadyBookedError(Exception):
    pass


class AppointmentNotFoundError(Exception):
    pass


def list_practitioners(db: Session) -> list[Practitioner]:
    return db.query(Practitioner).all()


def find_practitioner_by_name(db: Session, name: str) -> Practitioner | None:
    return db.query(Practitioner).filter(Practitioner.name.ilike(f"%{name}%")).first()


def list_available_slots(
    db: Session,
    practitioner_id: int | None = None,
    from_date: datetime | None = None,
    specialty: str | None = None,
) -> list[Slot]:
    query = db.query(Slot).filter(Slot.is_booked.is_(False))

    if practitioner_id is not None:
        query = query.filter(Slot.practitioner_id == practitioner_id)

    if specialty is not None:
        query = query.join(Practitioner, Slot.practitioner_id == Practitioner.id).filter(
            Practitioner.specialty.ilike(f"%{specialty}%")
        )

    if from_date is not None:
        query = query.filter(Slot.start_time >= from_date)

    return query.order_by(Slot.start_time).all()


def book_slot(
    db: Session, slot_id: int, patient_name: str, patient_email: str
) -> Appointment:
    slot = db.query(Slot).filter(Slot.id == slot_id).with_for_update().first()

    if slot is None:
        raise SlotNotFoundError(f"Creneau {slot_id} introuvable.")

    if slot.is_booked:
        raise SlotAlreadyBookedError(f"Creneau {slot_id} deja reserve.")

    slot.is_booked = True

    appointment = Appointment(
        slot_id=slot.id,
        patient_name=patient_name,
        patient_email=patient_email,
        status=AppointmentStatus.confirmed,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    subject, body = email_service.build_confirmation_email(
        patient_name=patient_name,
        practitioner_name=slot.practitioner.name,
        specialty=slot.practitioner.specialty,
        start_time=slot.start_time,
    )
    email_service.send_email(patient_email, subject, body)

    return appointment


def cancel_appointment(db: Session, appointment_id: int) -> Appointment:
    appointment = (
        db.query(Appointment).filter(Appointment.id == appointment_id).first()
    )

    if appointment is None:
        raise AppointmentNotFoundError(f"Rendez-vous {appointment_id} introuvable.")

    appointment.status = AppointmentStatus.cancelled
    appointment.slot.is_booked = False

    db.commit()
    db.refresh(appointment)

    subject, body = email_service.build_cancellation_email(
        patient_name=appointment.patient_name,
        practitioner_name=appointment.slot.practitioner.name,
        specialty=appointment.slot.practitioner.specialty,
        start_time=appointment.slot.start_time,
    )
    email_service.send_email(appointment.patient_email, subject, body)

    return appointment


def get_appointment(db: Session, appointment_id: int) -> Appointment | None:
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()


def get_appointments_by_email(db: Session, patient_email: str) -> list[Appointment]:
    return (
        db.query(Appointment)
        .join(Slot, Appointment.slot_id == Slot.id)
        .filter(Appointment.patient_email.ilike(patient_email))
        .order_by(Slot.start_time.desc())
        .all()
    )


def reschedule_appointment(db: Session, appointment_id: int, new_slot_id: int) -> Appointment:
    old_appointment = get_appointment(db, appointment_id)
    if old_appointment is None:
        raise AppointmentNotFoundError(f"Rendez-vous {appointment_id} introuvable.")

    if old_appointment.status != AppointmentStatus.confirmed:
        raise AppointmentNotFoundError(
            f"Le rendez-vous {appointment_id} n'est pas actif (statut : {old_appointment.status.value})."
        )

    new_appointment = book_slot(
        db, new_slot_id, old_appointment.patient_name, old_appointment.patient_email
    )
    cancel_appointment(db, old_appointment.id)

    return new_appointment


def to_appointment_history(appointment: Appointment) -> dict:
    return {
        "id": appointment.id,
        "patient_name": appointment.patient_name,
        "patient_email": appointment.patient_email,
        "status": appointment.status,
        "start_time": appointment.slot.start_time,
        "end_time": appointment.slot.end_time,
        "practitioner_name": appointment.slot.practitioner.name,
        "specialty": appointment.slot.practitioner.specialty,
    }


def list_all_appointments(db: Session) -> list[Appointment]:
    return db.query(Appointment).order_by(Appointment.created_at.desc()).all()


def get_admin_stats(db: Session) -> dict:
    total_appointments = db.query(Appointment).count()
    confirmed = (
        db.query(Appointment).filter(Appointment.status == AppointmentStatus.confirmed).count()
    )
    cancelled = (
        db.query(Appointment).filter(Appointment.status == AppointmentStatus.cancelled).count()
    )
    total_practitioners = db.query(Practitioner).count()

    cancellation_rate = (cancelled / total_appointments) if total_appointments > 0 else 0.0

    seven_days_ago = datetime.now() - timedelta(days=7)
    daily_counts = (
        db.query(sql_func.date(Appointment.created_at), sql_func.count(Appointment.id))
        .filter(Appointment.created_at >= seven_days_ago)
        .group_by(sql_func.date(Appointment.created_at))
        .order_by(sql_func.date(Appointment.created_at))
        .all()
    )

    return {
        "total_appointments": total_appointments,
        "confirmed_appointments": confirmed,
        "cancelled_appointments": cancelled,
        "cancellation_rate": round(cancellation_rate, 3),
        "total_practitioners": total_practitioners,
        "appointments_last_7_days": [
            {"date": str(day), "count": count} for day, count in daily_counts
        ],
    }