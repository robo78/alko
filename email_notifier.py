import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import settings_manager

def send_email(subject, body):
    """Sends an email using the configured settings."""
    settings = settings_manager.load_settings()

    smtp_server = settings.get("smtp_server")
    smtp_port = settings.get("smtp_port")
    smtp_user = settings.get("smtp_user")
    smtp_password = settings.get("smtp_password")
    recipient_email = settings.get("recipient_email")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password, recipient_email]):
        return "Błąd: Ustawienia e-mail nie są w pełni skonfigurowane."

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return "E-mail wysłany pomyślnie."
    except Exception as e:
        return f"Błąd podczas wysyłania e-maila: {e}"