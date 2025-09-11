import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# -------------------- Load secrets --------------------
EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = st.secrets["email"]["app_password"]

# -------------------- Function to send email --------------------
def send_notification(email, serial, file_name, file_content_bytes):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "New XML Key Request Received"

    body = f"A new XML key request has been submitted.\n\nEmail: {email}\nSerial: {serial}\nFile: {file_name}"
    msg.attach(MIMEText(body, "plain"))

    # Attach XML file
    attachment = MIMEApplication(file_content_bytes, _subtype="xml")
    attachment.add_header("Content-Disposition", "attachment", filename=file_name)
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
    return True

# -------------------- Handle requests --------------------
# Detect if EXE is sending POST multipart/form-data
# Streamlit runs in "run" mode, so use st.file_uploader for file
if st.experimental_get_query_params().get("api") == ["1"]:
    # EXE POST simulation
    st.warning("❌ Please do not access this endpoint via browser.")
    st.stop()
else:
    st.title("🔒 XML Key Backend")
    st.info("This backend only works via EXE. Browser submissions are blocked.")

# -------------------- Optional monitoring UI --------------------
# You can add file uploader if you want to test manually
# uploaded_file = st.file_uploader("Upload XML file (for testing only)", type="xml")
# if uploaded_file:
#     send_notification("test@example.com", "TEST123", uploaded_file.name, uploaded_file.read())
#     st.success("Email sent (test)")
