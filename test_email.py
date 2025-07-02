import smtplib
from email.mime.text import MIMEText

# Load your config (e.g., from environment variables)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "abhijitakadeveloper@gmail.com"
SMTP_PASSWORD = "hyoq oqjl ahfl qlbr"
FROM_EMAIL = "abhijitakadeveloper@gmail.com"

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

# Example usage
send_email("moviesabhijit@gmail.com", "Hello from Gmail SMTP", "This is a test email.")
