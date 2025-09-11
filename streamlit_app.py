# streamlit_app.py

import streamlit as st
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

st.set_page_config(page_title="XML Key Backend", page_icon="🔒")

EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = st.secrets["email"]["app_password"]  # Store safely in Streamlit secrets

def send_notification(user_email, serial, file_name, file_bytes):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "New XML Key Request Received"
    body = f"A new XML key request has been submitted.\n\nEmail: {user_email}\nSerial: {serial}\nFile: {file_name}"
    msg.attach(MIMEText(body, "plain"))
    attachment = MIMEApplication(file_bytes, _subtype="xml")
    attachment.add_header("Content-Disposition", "attachment", filename=file_name)
    msg.attach(attachment)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

st.title("XML Key Generator Tool - Request Backend")
st.write("Submit your XML for activation.")

with st.form("request_form", clear_on_submit=True):
    user_email = st.text_input("Your Email ID")
    serial = st.text_input("Device Full Serial Number")
    uploaded_file = st.file_uploader("Attach XML Exported File", type="xml")
    submitted = st.form_submit_button("Send Request")
    if submitted:
        if not user_email or not serial or not uploaded_file:
            st.error("Please fill all fields and attach an XML file.")
        else:
            file_name = uploaded_file.name
            file_bytes = uploaded_file.read()
            try:
                send_notification(user_email, serial, file_name, file_bytes)
                st.success("Request submitted successfully! You will receive confirmation via email.")
            except Exception as e:
                st.error(f"Failed to send request: {e}")
