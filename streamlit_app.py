import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# --- Load email app password from Streamlit secrets ---
EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = st.secrets["email"]["app_password"]  # securely stored in Streamlit secrets

# --- Function to send notification email with attachment ---
def send_notification(email: str, serial: str, uploaded_file):
    subject = "New XML Key Request Received"
    body = f"A new XML key request has been submitted.\n\nEmail: {email}\nSerial: {serial}\nFile: {uploaded_file.name}"
    
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Attach the uploaded XML file
    file_content = uploaded_file.read()
    attachment = MIMEApplication(file_content, _subtype="xml")
    attachment.add_header('Content-Disposition', 'attachment', filename=uploaded_file.name)
    msg.attach(attachment)

    # Send the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

# --- Streamlit UI ---
st.set_page_config(page_title="🔑 XML Key Request Backend", page_icon="🔒")
st.title("🔑 XML Key Request Backend")

st.subheader("Upload your XML file")
email = st.text_input("Email")
serial = st.text_input("Serial")
uploaded_file = st.file_uploader("Upload XML file", type=["xml"])

if st.button("Submit Request"):
    if not email or not serial or not uploaded_file:
        st.error("Please fill all fields and upload an XML file.")
    else:
        # Send notification email with the uploaded XML file attached
        send_notification(email, serial, uploaded_file)
        
        st.success("Request submitted successfully! You will receive the XML file via email.")
