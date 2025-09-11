import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json, base64

# -------------------- Load secrets --------------------
EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = st.secrets["email"]["app_password"]   # Gmail app password
EXE_TOKEN = st.secrets["backend"]["exe_token"]         # EXE token

# -------------------- Function to send email --------------------
def send_notification(email: str, serial: str, file_name: str, file_content_b64: str):
    try:
        subject = "New XML Key Request Received"
        body = f"A new XML key request has been submitted.\n\nEmail: {email}\nSerial: {serial}\nFile: {file_name}"

        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Attach the uploaded XML file (base64 decoded)
        attachment = MIMEApplication(base64.b64decode(file_content_b64), _subtype="xml")
        attachment.add_header("Content-Disposition", "attachment", filename=file_name)
        msg.attach(attachment)

        # Send the email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False
    return True

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="🔑 XML Key Request Backend", page_icon="🔒")
st.title("🔑 XML Key Request Backend")

# -------------------- Detect API request --------------------
query_params = st.query_params
if "api" in query_params:
    # Backend API mode
    try:
        # Read JSON POST body
        body = st.experimental_get_query_params().get("body")
        if body:
            data = json.loads(body[0])
        else:
            data = json.loads(st.experimental_get_query_params()["data"][0])  # fallback if using ?data=

        # Token check
        if data.get("token") != EXE_TOKEN:
            st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")
            st.stop()

        email = data.get("email")
        serial = data.get("serial")
        file_name = data.get("file_name")
        file_content_b64 = data.get("file_content")

        if not email or not serial or not file_name or not file_content_b64:
            st.error("Invalid data received.")
            st.stop()

        if send_notification(email, serial, file_name, file_content_b64):
            st.json({"status": "success", "message": "Request submitted successfully"})
        else:
            st.json({"status": "error", "message": "Failed to send email"})

    except Exception as e:
        st.json({"status": "error", "message": str(e)})
else:
    # Manual access blocked
    st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")

# -------------------- Optional manual upload UI --------------------
st.subheader("Manual Upload (for testing)")
email_input = st.text_input("Email")
serial_input = st.text_input("Serial")
uploaded_file = st.file_uploader("Upload XML file", type=["xml"])

if st.button("Submit Request"):
    if not email_input or not serial_input or not uploaded_file:
        st.error("Please fill all fields and upload an XML file.")
    else:
        file_content_b64 = base64.b64encode(uploaded_file.read()).decode()
        if send_notification(email_input, serial_input, uploaded_file.name, file_content_b64):
            st.success("Request submitted successfully!")
        else:
            st.error("Failed to send request.")
