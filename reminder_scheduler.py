import schedule
import time
import threading
import email_notifier
import settings_manager

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

    while True:
        schedule.run_pending()
        time.sleep(60) # Check every minute

def start_scheduler_thread():
    """Starts the scheduler in a background thread."""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()