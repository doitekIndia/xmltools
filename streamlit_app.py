import streamlit as st
import smtplib, json, base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from urllib.parse import unquote

# -------------------- Load secrets --------------------
EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = st.secrets["email"]["app_password"]
EXE_TOKEN = st.secrets["backend"]["exe_token"]
LICENSE_KEYS = st.secrets["backend"]["licenses"]

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

# -------------------- API Endpoint --------------------
st.set_page_config(page_title="🔑 XML Key Backend", page_icon="🔒")
st.title("🔑 XML Key Generator Backend")

query_params = st.query_params

# EXE client sends ?api=1&data=<URL-encoded JSON>
if query_params.get("api") == ["1"] and query_params.get("data"):
    try:
        data_json = unquote(query_params.get("data")[0])  # decode URL-encoded JSON
        data = json.loads(data_json)

        # Validate EXE token
        if data.get("token") != EXE_TOKEN:
            st.json({"status": "error", "message": "Invalid token. Buy the EXE."})
            st.stop()

        # Validate license key
        if data.get("license_key") not in LICENSE_KEYS.values():
            st.json({"status": "error", "message": "Invalid license key. Buy a valid license."})
            st.stop()

        # Extract submission
        email = data.get("email")
        serial = data.get("serial")
        file_name = data.get("file_name")
        file_content = data.get("file_content")  # must be base64

        # Send email notification with XML attachment
        send_notification(email, serial, file_name, file_content)

        st.json({"status": "success", "message": "Request submitted successfully"})

    except Exception as e:
        st.json({"status": "error", "message": str(e)})

else:
    st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")
