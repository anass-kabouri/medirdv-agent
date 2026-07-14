from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, appointments, auth, chat, practitioners, reminders, slots
from app.scheduler import start_scheduler

app = FastAPI(
    title="MediRDV Agent API",
    description="API de prise de rendez-vous avec agent IA (Claude + function calling)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(practitioners.router)
app.include_router(slots.router)
app.include_router(appointments.router)
app.include_router(chat.router)
app.include_router(reminders.router)
app.include_router(auth.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}