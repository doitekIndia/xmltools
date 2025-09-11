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

# Only show EXE endpoint if ?api=1 in URL
query_params = st.query_params
if query_params.get("api") == ["1"]:
    st.subheader("API is live (for EXE client)")
    try:
        # EXE client POST simulation
        data_raw = st.text_area("Paste JSON payload from EXE", "")
        if not data_raw:
            st.info("Waiting for data from EXE...")
        else:
            data = json.loads(data_raw)

            # Validate token
            if data.get("token") != EXE_TOKEN:
                st.json({"status": "error", "message": "Invalid token. Buy the EXE."})
                st.stop()

            # Validate license key
            if data.get("license_key") not in LICENSE_KEYS.values():
                st.json({"status": "error", "message": "Invalid license key. Buy a valid license."})
                st.stop()

            # Extract request data
            email = data.get("email")
            serial = data.get("serial")
            file_name = data.get("file_name")
            file_content = data.get("file_content")

            # Send email
            send_notification(email, serial, file_name, file_content)

            st.json({"status": "success", "message": "Request submitted successfully"})
    except Exception as e:
        st.json({"status": "error", "message": str(e)})
else:
    st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")
