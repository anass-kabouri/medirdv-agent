from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PractitionerOut
from app.services import scheduling

router = APIRouter(prefix="/practitioners", tags=["practitioners"])


@router.get("/", response_model=list[PractitionerOut])
def get_practitioners(db: Session = Depends(get_db)):
    return scheduling.list_practitioners(db)
