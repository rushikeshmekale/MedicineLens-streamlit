import smtplib
from email.message import EmailMessage

FOOTER = (
    "\n\n---\nSent by MedicineLens.\n"
    "This report is based only on the uploaded photos. It is not medical advice, "
    "a diagnosis, or a prescription. Please verify with a pharmacist or doctor."
)


def send_email(sender, app_password, to_email, user_name, report):
    try:
        msg = EmailMessage()
        msg["Subject"] = "💊 Your MedicineLens Report"
        msg["From"] = sender
        msg["To"] = to_email
        msg.set_content(f"Hi {user_name},\n\nHere is your medicine report:\n\n{report}{FOOTER}")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password.replace(" ", ""))
            server.send_message(msg)
        return True, "Email sent"
    except Exception as error:
        return False, str(error)