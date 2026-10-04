# 💊 MedicineLens

AI medicine label-reading assistant. Upload a photo of a medicine package, get a structured
label report, ask follow-up questions, and share the summary by email or WhatsApp.

**Not a medical device. Does not diagnose, prescribe, or give personal dosages.**

## Run locally
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py

## Secrets
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in your keys.

## Stack
Streamlit, Google Gemini (vision + chat), Gmail SMTP, Twilio WhatsApp