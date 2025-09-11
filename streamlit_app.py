import streamlit as st
import smtplib, json, base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# -------------------- Load secrets --------------------
EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = st.secrets["email"]["app_password"]

# -------------------- Function to send email --------------------
def send_notification(email, serial, file_name, file_content_b64):
    try:
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

        # Send email via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email sending failed: {e}")
        return False

# -------------------- Hidden backend API --------------------
# Only accept requests via ?api=1&data=JSON_BASE64
query_params = st.query_params

if "api" in query_params:
    try:
        data_json = query_params.get("data", [None])[0]
        if not data_json:
            st.json({"status": "error", "message": "No data provided"})
            st.stop()
        
        data = json.loads(data_json)

        # Required fields
        email = data.get("email")
        serial = data.get("serial")
        file_name = data.get("file_name")
        file_content = data.get("file_content")  # base64 encoded

        if not all([email, serial, file_name, file_content]):
            st.json({"status": "error", "message": "Missing required fields"})
            st.stop()

        # Send email
        success = send_notification(email, serial, file_name, file_content)
        if success:
            st.json({
                "status": "success",
                "message": "Request submitted successfully!\nYou will receive confirmation via email for processing soon."
            })
        else:
            st.json({"status": "error", "message": "Email sending failed"})

    except Exception as e:
        st.json({"status": "error", "message": str(e)})

else:
    # Manual UI blocked
    st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")
