import streamlit as st
from google import genai
from google.genai import types

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    ANALYZE_IMAGE_PROMPT,
    REPORT_REQUEST_PROMPT,
    SUMMARY_REQUEST_PROMPT,
)
from services.email_service import send_email
from services.whatsapp_service import send_whatsapp

st.set_page_config(page_title="MedicineLens", page_icon="💊", layout="centered")

# ---------- Secrets ----------
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
MODEL_NAME = st.secrets.get("MODEL_NAME", "gemini-3.8-flash")
GMAIL_ADDRESS = st.secrets.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = st.secrets.get("GMAIL_APP_PASSWORD", "")
TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = st.secrets.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = st.secrets.get("TWILIO_WHATSAPP_FROM", "")
TWILIO_CONTENT_SID = st.secrets.get("TWILIO_CONTENT_SID", "")

EMAIL_READY = bool(GMAIL_ADDRESS and GMAIL_APP_PASSWORD)
WHATSAPP_READY = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_FROM)


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# ---------- Helpers ----------
def new_chat():
    st.session_state.chat = gemini_client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    st.session_state.messages = []
    st.session_state.report = None
    st.session_state.has_image = False


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"], width=250)


def append_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})


def add_message(role, kind, content):
    append_message(role, kind, content)
    render_message(st.session_state.messages[-1])


def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry, something went wrong: {error}"


def is_error(text):
    return text.startswith("Sorry, something went wrong")


def generate_report(force=False):
    """Returns the report text (creates it if needed)."""
    if force or not st.session_state.report:
        with st.spinner("Preparing your medicine report..."):
            report = ask_gemini([REPORT_REQUEST_PROMPT])
        if is_error(report):
            return report
        st.session_state.report = report
        append_message("assistant", "text", report)
    return st.session_state.report


# ---------- Step 1: Onboarding ----------
if "onboarded" not in st.session_state:
    st.title("💊 MedicineLens")
    st.caption("Snap your medicine. Understand the label. Share the summary.")

    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        email = st.text_input("Email (to receive your reports)", placeholder="you@gmail.com")
        whatsapp_number = st.text_input(
            "WhatsApp number (optional, with country code)",
            placeholder="+91XXXXXXXXXX",
        )
        submitted = st.form_submit_button("Let's go 🚀")

    if submitted:
        if not name.strip() or not email.strip():
            st.warning("Please enter your name and email.")
        else:
            st.session_state.name = name.strip()
            st.session_state.email = email.strip()
            st.session_state.whatsapp_number = whatsapp_number.strip()
            new_chat()
            st.session_state.onboarded = True
            st.rerun()
    st.stop()

# ---------- Sidebar: actions ----------
with st.sidebar:
    st.header("💊 MedicineLens")
    st.caption(f"Logged in as {st.session_state.name}")
    has_image = st.session_state.has_image

    if st.button("📋 Generate report", disabled=not has_image, use_container_width=True):
        generate_report(force=True)
        st.rerun()

    if st.session_state.report:
        st.download_button(
            "⬇️ Download report (.txt)",
            data=st.session_state.report,
            file_name="medicinelens_report.txt",
            use_container_width=True,
        )

    if st.button(
        "📧 Send report to email",
        disabled=not (has_image and EMAIL_READY),
        use_container_width=True,
    ):
        report = generate_report()
        if is_error(report):
            st.error(report)
        else:
            ok, info = send_email(
                GMAIL_ADDRESS, GMAIL_APP_PASSWORD,
                st.session_state.email, st.session_state.name, report,
            )
            st.success(f"Sent to {st.session_state.email} ✅") if ok else st.error(f"Couldn't send: {info}")

    if st.button(
        "📲 Send summary to WhatsApp",
        disabled=not (has_image and WHATSAPP_READY and st.session_state.whatsapp_number),
        use_container_width=True,
    ):
        with st.spinner("Summarizing..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
        if is_error(summary):
            st.error(summary)
        else:
            ok, info = send_whatsapp(
                TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, TWILIO_CONTENT_SID,
                st.session_state.whatsapp_number, st.session_state.name, summary,
            )
            st.success("Sent! Check WhatsApp 📲") if ok else st.error(f"Couldn't send: {info}")

    if not EMAIL_READY:
        st.info("Add GMAIL_ADDRESS and GMAIL_APP_PASSWORD in secrets to enable email.")

    st.divider()
    if st.button("🔄 New medicine", use_container_width=True):
        new_chat()
        st.rerun()

    st.warning(
        "MedicineLens only reads label information. It is not a diagnosis or prescription. "
        "Always verify with a pharmacist or doctor."
    )

# ---------- Main chat ----------
st.title("💊 MedicineLens")

if not st.session_state.messages:
    add_message("assistant", "text", WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)

user_input = st.chat_input(
    "Attach medicine photo(s) or ask a question",
    accept_file="multiple",
    file_type=["jpg", "jpeg", "png", "webp"],
)

if user_input:
    photos = user_input.files or []
    text = user_input.text
    parts = []

    for photo in photos:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
        st.session_state.has_image = True

    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photos:
        parts.append(ANALYZE_IMAGE_PROMPT)

    with st.spinner("Reading the label..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)

    if photos:
        st.rerun()  # refresh so sidebar buttons become enabled