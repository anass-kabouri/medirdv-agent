from apscheduler.schedulers.background import BackgroundScheduler

from app.services.reminders import send_due_reminders

scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    scheduler.add_job(
        send_due_reminders,
        trigger="interval",
        hours=1,
        id="send_reminders",
        replace_existing=True,
    )
    scheduler.start()
    print("Scheduler de rappels demarre (verification toutes les heures).")