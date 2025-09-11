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
query_params = st.query_params

if "api" in query_params:
    # Only accept JSON POST/GET from EXE
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
        file_content = data.get("file_content")

        if not all([email, serial, file_name, file_content]):
            st.json({"status": "error", "message": "Missing required fields"})
            st.stop()

        # Optional: You can add email/serial verification here before sending
        # Example: only send if user email matches PayPal or other record
        # if not valid_user(email, serial): st.json({"status": "error", "message": "Unauthorized"}); st.stop()

        send_notification(email, serial, file_name, file_content)
        st.json({"status": "success", "message": "Request submitted successfully. Email sent for processing."})

    except Exception as e:
        st.json({"status": "error", "message": str(e)})

else:
    # Browser access blocked
    st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")
