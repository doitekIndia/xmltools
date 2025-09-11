import streamlit as st
import smtplib, json, base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# -------------------- Load secrets --------------------
EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = st.secrets["email"]["app_password"]
EXE_TOKEN = st.secrets["backend"]["exe_token"]

# Example license keys (in production, store securely!)
LICENSE_KEYS = st.secrets["backend"]["licenses"]  # e.g., {"USER1": "ABC123", "USER2": "XYZ456"}

# -------------------- Send email --------------------
def send_notification(email, serial, file_name, file_content_b64):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "New XML Key Request Received"
    body = f"Email: {email}\nSerial: {serial}\nFile: {file_name}"
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(base64.b64decode(file_content_b64), _subtype="xml")
    attachment.add_header("Content-Disposition", "attachment", filename=file_name)
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
    return True

# -------------------- API Endpoint --------------------
query_params = st.query_params
if "api" in query_params:
    try:
        data = st.experimental_get_query_params().get("data")
        if data:
            data = json.loads(data[0])
        else:
            st.json({"status": "error", "message": "No data provided"}); st.stop()

        # Check token
        if data.get("token") != EXE_TOKEN:
            st.json({"status": "error", "message": "Invalid token. Buy the EXE."}); st.stop()

        # Check license key
        license_key = data.get("license_key")
        if license_key not in LICENSE_KEYS.values():
            st.json({"status": "error", "message": "Invalid license key. Buy a valid license."})
            st.stop()

        # Process request
        email = data.get("email")
        serial = data.get("serial")
        file_name = data.get("file_name")
        file_content = data.get("file_content")

        send_notification(email, serial, file_name, file_content)
        st.json({"status": "success", "message": "Request submitted successfully"})
    except Exception as e:
        st.json({"status": "error", "message": str(e)})
else:
    st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")
