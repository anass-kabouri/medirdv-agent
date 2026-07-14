from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SlotOut
from app.services import scheduling

router = APIRouter(prefix="/slots", tags=["slots"])


@router.get("/available", response_model=list[SlotOut])
def get_available_slots(
    practitioner_id: int | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return scheduling.list_available_slots(db, practitioner_id, from_date)
