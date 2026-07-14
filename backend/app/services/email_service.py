import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


def send_email(to_email: str, subject: str, body: str) -> None:
    if not settings.smtp_user or not settings.smtp_password:
        print(f"[EMAIL DESACTIVE - pas de config SMTP] Destinataire: {to_email} | Sujet: {subject}")
        return

    message = MIMEMultipart()
    message["From"] = settings.smtp_from or settings.smtp_user
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
        print(f"Email envoye a {to_email} : {subject}")
    except Exception as e:
        print(f"ERREUR envoi email a {to_email} : {e}")


def build_confirmation_email(patient_name: str, practitioner_name: str, specialty: str, start_time) -> tuple[str, str]:
    subject = "Confirmation de votre rendez-vous - MediRDV"
    body = (
        f"Bonjour {patient_name},\n\n"
        f"Votre rendez-vous est confirme :\n"
        f"- Praticien : {practitioner_name} ({specialty})\n"
        f"- Date : {start_time.strftime('%d/%m/%Y a %H:%M')}\n\n"
        f"En cas d'empechement, merci de nous contacter pour annuler ou reporter.\n\n"
        f"A bientot,\nL'equipe MediRDV"
    )
    return subject, body


def build_cancellation_email(patient_name: str, practitioner_name: str, specialty: str, start_time) -> tuple[str, str]:
    subject = "Annulation de votre rendez-vous - MediRDV"
    body = (
        f"Bonjour {patient_name},\n\n"
        f"Votre rendez-vous du {start_time.strftime('%d/%m/%Y a %H:%M')} avec "
        f"{practitioner_name} ({specialty}) a bien ete annule.\n\n"
        f"N'hesitez pas a reprendre un nouveau rendez-vous quand vous le souhaitez.\n\n"
        f"A bientot,\nL'equipe MediRDV"
    )
    return subject, body


def build_reminder_email(patient_name: str, practitioner_name: str, specialty: str, start_time) -> tuple[str, str]:
    subject = "Rappel : votre rendez-vous approche - MediRDV"
    body = (
        f"Bonjour {patient_name},\n\n"
        f"Petit rappel : vous avez rendez-vous prochainement.\n"
        f"- Praticien : {practitioner_name} ({specialty})\n"
        f"- Date : {start_time.strftime('%d/%m/%Y a %H:%M')}\n\n"
        f"A bientot,\nL'equipe MediRDV"
    )
    return subject, body


def build_verification_email(patient_name: str, code: str) -> tuple[str, str]:
    subject = "Votre code de verification - MediRDV"
    body = (
        f"Bonjour {patient_name},\n\n"
        f"Voici votre code de verification : {code}\n\n"
        f"Ce code est valable 15 minutes.\n\n"
        f"Si vous n'etes pas a l'origine de cette demande, ignorez cet email.\n\n"
        f"A bientot,\nL'equipe MediRDV"
    )
    return subject, body