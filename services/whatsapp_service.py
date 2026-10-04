import json
from twilio.rest import Client as TwilioClient


def clean_text(text):
    if not text:
        return "No summary available."
    text = " ".join(text.split())
    return text[:1400] + "..." if len(text) > 1400 else text


def send_whatsapp(account_sid, auth_token, from_number, content_sid, to_number, user_name, summary):
    try:
        client = TwilioClient(account_sid, auth_token)
        summary = clean_text(summary)

        if content_sid:
            message = client.messages.create(
                from_=from_number,
                to=f"whatsapp:{to_number}",
                content_sid=content_sid,
                content_variables=json.dumps({"1": user_name, "2": summary}, ensure_ascii=False),
            )
        else:
            message = client.messages.create(
                from_=from_number,
                to=f"whatsapp:{to_number}",
                body=f"Hi {user_name}, here is your MedicineLens summary:\n\n{summary}",
            )
        return True, message.sid
    except Exception as error:
        return False, str(error)