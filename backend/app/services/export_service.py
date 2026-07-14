import csv
import io
import os
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.services import scheduling


def appointments_to_csv(db):
    appointments = scheduling.list_all_appointments(db)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([settings.clinic_name])
    writer.writerow([f"Export genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}"])
    writer.writerow([])
    writer.writerow(["ID", "Patient", "Email", "Praticien", "Specialite", "Date", "Statut"])

    for a in appointments:
        writer.writerow(
            [
                a.id,
                a.patient_name,
                a.patient_email,
                a.slot.practitioner.name,
                a.slot.practitioner.specialty,
                a.slot.start_time.strftime("%Y-%m-%d %H:%M"),
                a.status.value,
            ]
        )

    return output.getvalue()


def _build_pdf_header(styles):
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, Spacer

    elements = []

    centered_title = styles["Title"].clone("CenteredTitle")
    centered_title.alignment = TA_CENTER

    centered_subtitle = styles["Normal"].clone("CenteredSubtitle")
    centered_subtitle.alignment = TA_CENTER
    centered_subtitle.textColor = "#6b7280"

    logo_path = settings.clinic_logo_path
    if logo_path and os.path.isfile(logo_path):
        try:
            logo = Image(logo_path, width=28 * mm, height=28 * mm)
            logo.hAlign = "CENTER"
            elements.append(logo)
            elements.append(Spacer(1, 6))
        except Exception:
            pass

    elements.append(Paragraph(settings.clinic_name, centered_title))
    elements.append(
        Paragraph(
            f"Export genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}",
            centered_subtitle,
        )
    )
    elements.append(Spacer(1, 16))

    return elements


def appointments_to_pdf(db):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle

    appointments = scheduling.list_all_appointments(db)
    styles = getSampleStyleSheet()

    data = [["ID", "Patient", "Praticien", "Specialite", "Date", "Statut"]]
    for a in appointments:
        data.append(
            [
                str(a.id),
                a.patient_name,
                a.slot.practitioner.name,
                a.slot.practitioner.specialty,
                a.slot.start_time.strftime("%Y-%m-%d %H:%M"),
                a.status.value,
            ]
        )

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f2f5")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#9ca3af"))
        canvas.drawCentredString(
            A4[0] / 2, 15, f"{settings.clinic_name} - Page {doc.page}"
        )
        canvas.restoreState()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=30,
        title=f"Rendez-vous - {settings.clinic_name}",
    )

    elements = _build_pdf_header(styles)
    elements.append(Spacer(1, 4))
    elements.append(table)

    doc.build(elements, onFirstPage=_footer, onLaterPages=_footer)

    buffer.seek(0)
    return buffer.getvalue()