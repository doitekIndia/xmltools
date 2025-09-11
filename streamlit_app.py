import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
import base64

# --- Load email app password from Streamlit secrets ---
EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = st.secrets["email"]["app_password"]

# --- Secret token for EXE authentication ---
EXE_TOKEN = st.secrets["backend"]["exe_token"]  # securely stored in Streamlit secrets

# --- Function to send notification email with attachment ---
def send_notification(email: str, serial: str, file_name: str, file_content: bytes):
    subject = "New XML Key Request Received"
    body = f"A new XML key request has been submitted.\n\nEmail: {email}\nSerial: {serial}\nFile: {file_name}"
    
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(file_content, _subtype="xml")
    attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

# --- Streamlit UI ---
st.set_page_config(page_title="🔑 XML Key Request Backend", page_icon="🔒")
st.title("🔑 XML Key Request Backend")

# --- Detect API requests from EXE ---
query_params = st.experimental_get_query_params()
if "api" in query_params:
    import sys
    body = sys.stdin.read()
    try:
        data = json.loads(body)
        # --- Check EXE token ---
        if data.get("token") != EXE_TOKEN:
            st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")
            sys.exit()

        file_name = data.get("file_name", "uploaded.xml")
        file_content_b64 = data.get("file_content")
        file_content = base64.b64decode(file_content_b64)
        send_notification(data["email"], data["serial"], file_name, file_content)
        print(json.dumps({"status": "success"}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

else:
    # --- Manual browser upload disabled ---
    st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")
