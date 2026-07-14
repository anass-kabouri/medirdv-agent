from app.services import export_service, scheduling


def test_appointments_to_csv_contains_header_and_data(db_session, slot):
    scheduling.book_slot(db_session, slot.id, "Jean Dupont", "jean@example.com")

    csv_content = export_service.appointments_to_csv(db_session)

    assert "ID,Patient,Email,Praticien,Specialite,Date,Statut" in csv_content
    assert "Jean Dupont" in csv_content
    assert "jean@example.com" in csv_content


def test_appointments_to_csv_includes_clinic_name_header(db_session):
    csv_content = export_service.appointments_to_csv(db_session)

    lines = csv_content.strip().split("\r\n")
    assert lines[0] == "MediRDV"
    assert "Export genere le" in lines[1]


def test_appointments_to_csv_empty_database_has_no_data_rows(db_session):
    csv_content = export_service.appointments_to_csv(db_session)

    lines = [line for line in csv_content.strip().split("\r\n") if line]
    assert len(lines) == 3


def test_appointments_to_pdf_returns_valid_pdf_bytes(db_session, slot):
    scheduling.book_slot(db_session, slot.id, "Jean Dupont", "jean@example.com")

    pdf_bytes = export_service.appointments_to_pdf(db_session)

    assert pdf_bytes[:5] == b"%PDF-"
    assert len(pdf_bytes) > 0