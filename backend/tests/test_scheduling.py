import pytest

from app.services import scheduling


def test_list_available_slots_returns_free_slot(db_session, slot):
    available = scheduling.list_available_slots(db_session)
    assert slot in available


def test_list_available_slots_excludes_booked(db_session, slot):
    slot.is_booked = True
    db_session.commit()

    available = scheduling.list_available_slots(db_session)
    assert slot not in available


def test_book_slot_success(db_session, slot):
    appointment = scheduling.book_slot(db_session, slot.id, "Jean Dupont", "jean@example.com")

    assert appointment.id is not None
    assert appointment.status.value == "confirmed"
    assert appointment.patient_name == "Jean Dupont"

    db_session.refresh(slot)
    assert slot.is_booked is True


def test_book_slot_not_found_raises(db_session):
    with pytest.raises(scheduling.SlotNotFoundError):
        scheduling.book_slot(db_session, 9999, "Jean Dupont", "jean@example.com")


def test_book_slot_already_booked_raises(db_session, slot):
    scheduling.book_slot(db_session, slot.id, "Jean Dupont", "jean@example.com")

    with pytest.raises(scheduling.SlotAlreadyBookedError):
        scheduling.book_slot(db_session, slot.id, "Marie Curie", "marie@example.com")


def test_cancel_appointment_frees_the_slot(db_session, slot):
    appointment = scheduling.book_slot(db_session, slot.id, "Jean Dupont", "jean@example.com")

    cancelled = scheduling.cancel_appointment(db_session, appointment.id)

    assert cancelled.status.value == "cancelled"
    db_session.refresh(slot)
    assert slot.is_booked is False


def test_cancel_appointment_not_found_raises(db_session):
    with pytest.raises(scheduling.AppointmentNotFoundError):
        scheduling.cancel_appointment(db_session, 9999)


def test_find_practitioner_by_name_partial_match(db_session, practitioner):
    found = scheduling.find_practitioner_by_name(db_session, "martin")
    assert found is not None
    assert found.id == practitioner.id


def test_find_practitioner_by_name_no_match(db_session):
    found = scheduling.find_practitioner_by_name(db_session, "Personne Inexistante")
    assert found is None


def test_list_available_slots_filters_by_specialty(db_session, practitioner, slot):
    matching = scheduling.list_available_slots(db_session, specialty="Generaliste")
    assert slot in matching

    non_matching = scheduling.list_available_slots(db_session, specialty="Cardiologie")
    assert slot not in non_matching


def test_get_appointments_by_email_returns_history(db_session, slot):
    scheduling.book_slot(db_session, slot.id, "Jean Dupont", "jean@example.com")

    history = scheduling.get_appointments_by_email(db_session, "jean@example.com")
    assert len(history) == 1
    assert history[0].patient_email == "jean@example.com"


def test_get_appointments_by_email_no_match_returns_empty(db_session):
    history = scheduling.get_appointments_by_email(db_session, "personne@example.com")
    assert history == []


def test_reschedule_appointment_moves_to_new_slot(db_session, practitioner, slot):
    from datetime import timedelta

    from app.models import Slot

    other_slot = Slot(
        practitioner_id=practitioner.id,
        start_time=slot.start_time + timedelta(hours=1),
        end_time=slot.end_time + timedelta(hours=1),
        is_booked=False,
    )
    db_session.add(other_slot)
    db_session.commit()
    db_session.refresh(other_slot)

    original = scheduling.book_slot(db_session, slot.id, "Jean Dupont", "jean@example.com")

    moved = scheduling.reschedule_appointment(db_session, original.id, other_slot.id)

    assert moved.slot_id == other_slot.id
    assert moved.status.value == "confirmed"

    db_session.refresh(slot)
    db_session.refresh(other_slot)
    assert slot.is_booked is False
    assert other_slot.is_booked is True


def test_reschedule_appointment_not_found_raises(db_session, slot):
    with pytest.raises(scheduling.AppointmentNotFoundError):
        scheduling.reschedule_appointment(db_session, 9999, slot.id)


def test_list_all_appointments_returns_everyone(db_session, practitioner, slot):
    from datetime import timedelta

    from app.models import Slot

    other_slot = Slot(
        practitioner_id=practitioner.id,
        start_time=slot.start_time + timedelta(hours=1),
        end_time=slot.end_time + timedelta(hours=1),
        is_booked=False,
    )
    db_session.add(other_slot)
    db_session.commit()
    db_session.refresh(other_slot)

    scheduling.book_slot(db_session, slot.id, "Jean Dupont", "jean@example.com")
    scheduling.book_slot(db_session, other_slot.id, "Marie Curie", "marie@example.com")

    all_appointments = scheduling.list_all_appointments(db_session)
    assert len(all_appointments) == 2


def test_get_admin_stats_counts_confirmed_and_cancelled(db_session, slot):
    appointment = scheduling.book_slot(db_session, slot.id, "Jean Dupont", "jean@example.com")
    scheduling.cancel_appointment(db_session, appointment.id)

    stats = scheduling.get_admin_stats(db_session)

    assert stats["total_appointments"] == 1
    assert stats["confirmed_appointments"] == 0
    assert stats["cancelled_appointments"] == 1
    assert stats["cancellation_rate"] == 1.0


def test_get_admin_stats_empty_database(db_session):
    stats = scheduling.get_admin_stats(db_session)

    assert stats["total_appointments"] == 0
    assert stats["cancellation_rate"] == 0.0