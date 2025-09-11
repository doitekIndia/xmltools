import streamlit as st
import smtplib
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# -------------------- Load secrets --------------------
EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = st.secrets["email"]["app_password"]

# -------------------- Function to send email --------------------
def send_notification(email, serial, file_name, file_content_b64):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "New XML Key Request Received"

    body = f"A new XML key request has been submitted.\n\nEmail: {email}\nSerial: {serial}\nFile: {file_name}"
    msg.attach(MIMEText(body, "plain"))

    # Attach uploaded XML
    attachment = MIMEApplication(base64.b64decode(file_content_b64), _subtype="xml")
    attachment.add_header("Content-Disposition", "attachment", filename=file_name)
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
    return True

# -------------------- API Endpoint --------------------
# Only allow POST JSON requests from EXE
if st.session_state.get("request_method", None) != "POST":
    st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")
    st.stop()

# Attempt to parse JSON POST body
try:
    data_raw = st.experimental_get_query_params().get("data", [None])[0]  # optional GET fallback
    if not data_raw:
        data = st.experimental_get_query_params().get("data")  # fallback
        if not data:
            st.json({"status": "error", "message": "Only EXE POST requests are allowed"})
            st.stop()
    else:
        data = json.loads(data_raw)

except Exception as e:
    st.json({"status": "error", "message": f"Failed to parse request: {e}"})
    st.stop()

# -------------------- Extract fields --------------------
email = data.get("email")
serial = data.get("serial")
file_name = data.get("file_name")
file_content = data.get("file_content")

if not all([email, serial, file_name, file_content]):
    st.json({"status": "error", "message": "Missing required fields"})
    st.stop()

# Optional: validate email/serial (e.g., check PayPal match)
# if not valid_user(email, serial): st.json({"status":"error","message":"Unauthorized"}); st.stop()

# -------------------- Send email --------------------
try:
    send_notification(email, serial, file_name, file_content)
    st.json({
        "status": "success",
        "message": "Request submitted successfully!\nYou will receive confirmation via email for processing soon."
    })
except Exception as e:
    st.json({"status": "error", "message": f"Failed to send email: {e}"})
