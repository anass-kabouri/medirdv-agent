from datetime import datetime, time, timedelta

from app.database import Base, SessionLocal, engine
from app.models import Practitioner, Slot

PRACTITIONERS = [
    {"name": "Dr. Amine Bensouda", "specialty": "Medecine generale"},
    {"name": "Dr. Sarah El Fassi", "specialty": "Cardiologie"},
    {"name": "Dr. Karim Idrissi", "specialty": "Dermatologie"},
]

NUMBER_OF_DAYS = 14
DAY_START = time(9, 0)
DAY_END = time(17, 0)
SLOT_DURATION_MINUTES = 30


def generate_slots_for_day(day: datetime) -> list[tuple[datetime, datetime]]:
    slots = []
    current = datetime.combine(day.date(), DAY_START)
    end_of_day = datetime.combine(day.date(), DAY_END)

    while current < end_of_day:
        slot_end = current + timedelta(minutes=SLOT_DURATION_MINUTES)
        slots.append((current, slot_end))
        current = slot_end

    return slots


def seed():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Practitioner).count() > 0:
            print("Des praticiens existent deja, seed annule pour eviter les doublons.")
            return

        practitioners = [Practitioner(**p) for p in PRACTITIONERS]
        db.add_all(practitioners)
        db.commit()
        for p in practitioners:
            db.refresh(p)

        today = datetime.now()
        total_slots = 0

        for practitioner in practitioners:
            for day_offset in range(NUMBER_OF_DAYS):
                day = today + timedelta(days=day_offset)
                if day.weekday() >= 5:
                    continue

                for start, end in generate_slots_for_day(day):
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
        print(f"Seed termine : {len(practitioners)} praticiens, {total_slots} creneaux crees.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
