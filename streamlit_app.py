import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import base64

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

# -------------------- Backend API --------------------
# Only accept requests from EXE; hide UI from browser
st.set_page_config(page_title="XML Key Backend", page_icon="🔒", layout="centered")

# Hide Streamlit elements
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Only accept POST via st.file_uploader + fields (EXE will submit multipart/form-data)
if st.session_state.get("is_post", False):
    data = st.session_state.get("post_data", {})
    email = data.get("email")
    serial = data.get("serial")
    file_name = data.get("file_name")
    file_content = data.get("file_content")
    
    if not all([email, serial, file_name, file_content]):
        st.json({"status": "error", "message": "Missing required fields"})
    else:
        try:
            send_notification(email, serial, file_name, file_content)
            st.json({"status": "success", "message": "Request submitted successfully. You will receive email confirmation soon."})
        except Exception as e:
            st.json({"status": "error", "message": str(e)})

else:
    # Block browser access
    st.error("❌ Please buy XML Key Generator EXE from: https://doitek.streamlit.app/")
