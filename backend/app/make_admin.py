import sys

from app.database import SessionLocal
from app.models import Patient


def make_admin(email: str) -> None:
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.email.ilike(email)).first()
        if patient is None:
            print(f"Aucun compte trouve pour {email}.")
            return

        if not patient.is_verified:
            print(f"Attention : le compte {email} n'est pas encore verifie.")

        patient.is_admin = True
        db.commit()
        print(f"{email} est maintenant administrateur.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage : python -m app.make_admin email@exemple.com")
        sys.exit(1)

    make_admin(sys.argv[1])