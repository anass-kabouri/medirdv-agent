"""
Tools de l'agent : chaque tool est une fonction metier exposee a Claude.
"""

from datetime import datetime

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services import scheduling


class ListPractitionersInput(BaseModel):
    pass


class CheckAvailabilityInput(BaseModel):
    practitioner_name: str | None = Field(
        default=None,
        description="Nom (ou partie du nom) du praticien, ex: 'Sarah' ou 'Dr. Sarah El Fassi'. "
        "Laisser vide pour voir les creneaux de tous les praticiens.",
    )
    specialty: str | None = Field(
        default=None,
        description="Specialite recherchee, ex: 'Cardiologie', 'Dermatologie'. "
        "A utiliser quand le patient demande un type de praticien plutot qu'un nom precis. "
        "Ignore si practitioner_name est deja fourni.",
    )
    from_date: str | None = Field(
        default=None,
        description="Date minimale au format YYYY-MM-DD. Laisser vide pour partir d'aujourd'hui.",
    )


class BookAppointmentInput(BaseModel):
    slot_id: int = Field(
        description="L'id exact du creneau a reserver, obtenu via l'outil check_availability. "
        "Ne jamais inventer un id."
    )
    patient_name: str = Field(description="Nom complet du patient")
    patient_email: str = Field(description="Adresse email du patient, pour la confirmation")


class RescheduleAppointmentInput(BaseModel):
    appointment_id: int = Field(description="L'id du rendez-vous existant a deplacer")
    new_slot_id: int = Field(
        description="L'id du nouveau creneau souhaite, obtenu via check_availability"
    )


class HistoryInput(BaseModel):
    patient_email: str = Field(description="Email du patient dont on veut l'historique")


class CancelAppointmentInput(BaseModel):
    appointment_id: int = Field(description="L'id du rendez-vous a annuler")


def build_tools(db: Session) -> list[StructuredTool]:
    def _list_practitioners() -> str:
        practitioners = scheduling.list_practitioners(db)
        if not practitioners:
            return "Aucun praticien enregistre."
        return "\n".join(f"- id={p.id}: {p.name} ({p.specialty})" for p in practitioners)

    def _check_availability(
        practitioner_name: str | None = None,
        specialty: str | None = None,
        from_date: str | None = None,
    ) -> str:
        practitioner_id = None
        if practitioner_name:
            match = scheduling.find_practitioner_by_name(db, practitioner_name)
            if match is None:
                return (
                    f"Aucun praticien ne correspond a '{practitioner_name}'. "
                    "Utilise list_practitioners pour voir les noms exacts."
                )
            practitioner_id = match.id

        parsed_date = datetime.now()
        if from_date:
            try:
                candidate = datetime.fromisoformat(from_date)
            except ValueError:
                return f"Date invalide : '{from_date}'. Utilise le format YYYY-MM-DD."
            parsed_date = max(candidate, parsed_date)

        effective_specialty = None if practitioner_id else specialty

        slots = scheduling.list_available_slots(
            db, practitioner_id, parsed_date, effective_specialty
        )
        if not slots:
            return "Aucun creneau disponible pour ces criteres."

        shown = slots[:20]
        lines = [
            f"- id={s.id}: praticien_id={s.practitioner_id}, "
            f"du {s.start_time.strftime('%Y-%m-%d %H:%M')} a {s.end_time.strftime('%H:%M')}"
            for s in shown
        ]
        if len(slots) > 20:
            lines.append(f"(+{len(slots) - 20} autres creneaux, affine la recherche si besoin)")
        return "\n".join(lines)

    def _book_appointment(slot_id: int, patient_name: str, patient_email: str) -> str:
        try:
            appt = scheduling.book_slot(db, slot_id, patient_name, patient_email)
            return f"Rendez-vous confirme ! id={appt.id}, statut={appt.status.value}."
        except scheduling.SlotNotFoundError:
            return f"Erreur : le creneau {slot_id} n'existe pas."
        except scheduling.SlotAlreadyBookedError:
            return (
                f"Erreur : le creneau {slot_id} est deja reserve. "
                "Propose un autre creneau au patient via check_availability."
            )

    def _cancel_appointment(appointment_id: int) -> str:
        try:
            appt = scheduling.cancel_appointment(db, appointment_id)
            return f"Rendez-vous {appt.id} annule avec succes."
        except scheduling.AppointmentNotFoundError:
            return f"Erreur : le rendez-vous {appointment_id} n'existe pas."

    def _reschedule_appointment(appointment_id: int, new_slot_id: int) -> str:
        try:
            new_appt =scheduling.reschedule_appointment(db, appointment_id, new_slot_id)
            return (
                f"Rendez-vous deplace avec succes ! Nouveau rendez-vous id={new_appt.id}, "
                f"statut={new_appt.status.value}."
            )
        except scheduling.AppointmentNotFoundError as e:
            return f"Erreur : {e}"
        except scheduling.SlotNotFoundError:
            return f"Erreur : le nouveau creneau {new_slot_id} n'existe pas."
        except scheduling.SlotAlreadyBookedError:
            return (
                f"Erreur : le creneau {new_slot_id} est deja reserve. "
                "Le rendez-vous d'origine n'a pas ete modifie. Propose un autre creneau."
            )

    def _get_history(patient_email: str) -> str:
        appointments = scheduling.get_appointments_by_email(db, patient_email)
        if not appointments:
            return f"Aucun rendez-vous trouve pour {patient_email}."

        lines = [
            f"- id={a.id}: {a.slot.practitioner.name} ({a.slot.practitioner.specialty}), "
            f"le {a.slot.start_time.strftime('%Y-%m-%d %H:%M')}, statut={a.status.value}"
            for a in appointments
        ]
        return "\n".join(lines)

    return [
        StructuredTool.from_function(
            func=_list_practitioners,
            name="list_practitioners",
            description=(
                "Liste tous les praticiens disponibles avec leur specialite. "
                "A utiliser si l'utilisateur ne precise pas de praticien ou demande qui est disponible."
            ),
            args_schema=ListPractitionersInput,
        ),
        StructuredTool.from_function(
            func=_check_availability,
            name="check_availability",
            description=(
                "Verifie les creneaux disponibles, filtres optionnellement par nom de "
                "praticien et date de debut. A utiliser AVANT toute reservation."
            ),
            args_schema=CheckAvailabilityInput,
        ),
        StructuredTool.from_function(
            func=_book_appointment,
            name="book_appointment",
            description=(
                "Reserve un creneau specifique pour un patient. Necessite l'id exact du "
                "creneau obtenu via check_availability, jamais invente."
            ),
            args_schema=BookAppointmentInput,
        ),
        StructuredTool.from_function(
            func=_cancel_appointment,
            name="cancel_appointment",
            description="Annule un rendez-vous existant a partir de son id.",
            args_schema=CancelAppointmentInput,
        ),
        StructuredTool.from_function(
            func=_reschedule_appointment,
            name="reschedule_appointment",
            description=(
                "Deplace un rendez-vous existant vers un nouveau creneau (annule l'ancien "
                "et reserve le nouveau en une seule action). Utilise check_availability "
                "d'abord pour trouver l'id du nouveau creneau souhaite."
            ),
            args_schema=RescheduleAppointmentInput,
        ),
        StructuredTool.from_function(
            func=_get_history,
            name="get_patient_history",
            description=(
                "Recupere l'historique complet des rendez-vous (passes et a venir) d'un "
                "patient a partir de son email. Utile si le patient demande a voir ou "
                "gerer ses rendez-vous existants."
            ),
            args_schema=HistoryInput,
        ),
    ]