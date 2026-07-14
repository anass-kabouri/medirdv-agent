import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Practitioner, Slot


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def practitioner(db_session):
    p = Practitioner(name="Dr. Test Martin", specialty="Generaliste")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture()
def slot(db_session, practitioner):
    start = datetime.now() + timedelta(days=1)
    s = Slot(
        practitioner_id=practitioner.id,
        start_time=start,
        end_time=start + timedelta(minutes=30),
        is_booked=False,
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


@pytest.fixture(autouse=True)
def disable_real_emails(monkeypatch):
    monkeypatch.setattr("app.services.email_service.send_email", lambda *args, **kwargs: None)


@pytest.fixture(autouse=True)
def isolate_clinic_settings(monkeypatch):
    monkeypatch.setattr("app.config.settings.clinic_name", "MediRDV")
    monkeypatch.setattr("app.config.settings.clinic_logo_path", "")