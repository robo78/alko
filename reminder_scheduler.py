import schedule
import time
import threading
import email_notifier
import settings_manager


_stop_event = threading.Event()
_scheduler_thread = None


def send_reminder_email():
    """Sends a predefined reminder email."""
    settings = settings_manager.load_settings()
    if settings.get("reminders_enabled"):
        subject = "Codzienne przypomnienie - Dzienniczek Głodów Alkoholowych"
        body = "Pamiętaj, aby dzisiaj uzupełnić swój dzienniczek. Każdy wpis to krok w dobrą stronę!"
        email_notifier.send_email(subject, body)


def run_scheduler():
    """Runs the scheduler loop."""
    settings = settings_manager.load_settings()
    reminder_time = settings.get("reminder_time", "10:00")

    schedule.every().day.at(reminder_time).do(send_reminder_email)

    while not _stop_event.is_set():
        schedule.run_pending()
        if _stop_event.wait(60):
            break


def start_scheduler_thread():
    """Starts the scheduler in a background thread."""
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    _scheduler_thread.start()


def stop_scheduler_thread():
    """Stops the scheduler loop and waits briefly for the thread to exit."""
    global _scheduler_thread
    if not _scheduler_thread:
        return
    _stop_event.set()
    if _scheduler_thread.is_alive():
        _scheduler_thread.join(timeout=2)
    schedule.clear()
    _scheduler_thread = None
