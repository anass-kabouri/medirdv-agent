from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models import AppointmentStatus


class PractitionerOut(BaseModel):
    id: int
    name: str
    specialty: str

    class Config:
        from_attributes = True


class SlotOut(BaseModel):
    id: int
    practitioner_id: int
    start_time: datetime
    end_time: datetime
    is_booked: bool

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    slot_id: int
    patient_name: str
    patient_email: EmailStr


class AppointmentOut(BaseModel):
    id: int
    slot_id: int
    patient_name: str
    patient_email: str
    status: AppointmentStatus
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


class AppointmentHistoryOut(BaseModel):
    id: int
    patient_name: str
    patient_email: str
    status: AppointmentStatus
    start_time: datetime
    end_time: datetime
    practitioner_name: str
    specialty: str


class PatientRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class PatientOut(BaseModel):
    id: int
    name: str
    email: str
    is_verified: bool
    is_admin: bool

    class Config:
        from_attributes = True


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str


class ResendCodeRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    patient: PatientOut

class DailyCount(BaseModel):
    date: str
    count: int


class AdminStatsOut(BaseModel):
    total_appointments: int
    confirmed_appointments: int
    cancelled_appointments: int
    cancellation_rate: float
    total_practitioners: int
    appointments_last_7_days: list[DailyCount]