import argparse
from datetime import datetime, time, timedelta

from app.database import SessionLocal
from app.models import Practitioner, Slot

DAY_START = time(9, 0)
DAY_END = time(17, 0)
SLOT_DURATION_MINUTES = 30


def _generate_slots_for_day(day):
    slots = []
    current = datetime.combine(day.date(), DAY_START)
    end_of_day = datetime.combine(day.date(), DAY_END)
    while current < end_of_day:
        slot_end = current + timedelta(minutes=SLOT_DURATION_MINUTES)
        slots.append((current, slot_end))
        current = slot_end
    return slots


def add_practitioner(name, specialty, days=14):
    db = SessionLocal()
    try:
        existing = db.query(Practitioner).filter(Practitioner.name.ilike(name)).first()
        if existing is not None:
            print(f"Un praticien nomme '{name}' existe deja (id={existing.id}).")
            return

        practitioner = Practitioner(name=name, specialty=specialty)
        db.add(practitioner)
        db.commit()
        db.refresh(practitioner)

        today = datetime.now()
        total_slots = 0
        for day_offset in range(days):
            day = today + timedelta(days=day_offset)
            if day.weekday() >= 5:
                continue
            for start, end in _generate_slots_for_day(day):
                db.add(
                    Slot(
                        practitioner_id=practitioner.id,
                        start_time=start,
                        end_time=end,
                        is_booked=False,
                    )
                )
                total_slots += 1

        db.commit()
        print(f"Praticien '{name}' ({specialty}) cree avec {total_slots} creneaux sur {days} jours.")
    finally:
        db.close()


def _extend_slots_for(db, practitioner, days):
    last_slot = (
        db.query(Slot)
        .filter(Slot.practitioner_id == practitioner.id)
        .order_by(Slot.start_time.desc())
        .first()
    )
    start_from = (last_slot.start_time + timedelta(days=1)) if last_slot else datetime.now()

    total_slots = 0
    for day_offset in range(days):
        day = start_from + timedelta(days=day_offset)
        if day.weekday() >= 5:
            continue
        for start, end in _generate_slots_for_day(day):
            db.add(
                Slot(
                    practitioner_id=practitioner.id,
                    start_time=start,
                    end_time=end,
                    is_booked=False,
                )
            )
            total_slots += 1

    db.commit()
    return total_slots


def extend_one(name, days=14):
    db = SessionLocal()
    try:
        practitioner = db.query(Practitioner).filter(Practitioner.name.ilike(f"%{name}%")).first()
        if practitioner is None:
            print(f"Aucun praticien trouve pour '{name}'.")
            return
        total = _extend_slots_for(db, practitioner, days)
        print(f"{total} nouveaux creneaux ajoutes pour {practitioner.name}.")
    finally:
        db.close()


def extend_all(days=14):
    db = SessionLocal()
    try:
        practitioners = db.query(Practitioner).all()
        for practitioner in practitioners:
            total = _extend_slots_for(db, practitioner, days)
            print(f"{total} nouveaux creneaux ajoutes pour {practitioner.name}.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gestion des praticiens et de leurs creneaux.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Ajouter un nouveau praticien")
    add_parser.add_argument("name")
    add_parser.add_argument("specialty")
    add_parser.add_argument("--days", type=int, default=14)

    extend_parser = subparsers.add_parser("extend", help="Prolonger les creneaux d'un praticien")
    extend_parser.add_argument("name")
    extend_parser.add_argument("--days", type=int, default=14)

    extend_all_parser = subparsers.add_parser(
        "extend-all", help="Prolonger les creneaux de tous les praticiens"
    )
    extend_all_parser.add_argument("--days", type=int, default=14)

    args = parser.parse_args()

    if args.command == "add":
        add_practitioner(args.name, args.specialty, args.days)
    elif args.command == "extend":
        extend_one(args.name, args.days)
    elif args.command == "extend-all":
        extend_all(args.days)