import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

st.set_page_config(page_title="XML Key Backend", page_icon="🔒")

# -------------------------------
# CONFIG
EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = st.secrets["email"]["app_password"]  # Stored in Streamlit secrets
# -------------------------------

# In-memory user credits (for demo; replace with DB in production)
if "credits" not in st.session_state:
    st.session_state.credits = {}  # {email: credits}

# Function to send email
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

# ------------------------------------
st.title("XML Key Generator Tool - Credit Based")
st.write("Submit your XML for activation. Credits required.")

# Simulate purchase credits
st.subheader("Buy Credits")
st.info("💳 In real version, integrate PayPal API. For now, choose option to simulate purchase.")
if st.button("Buy 1 Credit ($20)"):
    user = st.session_state.get("last_user")
    if user:
        st.session_state.credits[user] = st.session_state.credits.get(user, 0) + 1
        st.success("Added 1 credit to your account!")
if st.button("Buy 20 Credits ($100)"):
    user = st.session_state.get("last_user")
    if user:
        st.session_state.credits[user] = st.session_state.credits.get(user, 0) + 20
        st.success("Added 20 credits to your account!")

# ------------------------------------
st.subheader("Submit XML Request")

with st.form("request_form", clear_on_submit=True):
    user_email = st.text_input("Your Email ID")
    serial = st.text_input("Device Full Serial Number")
    uploaded_file = st.file_uploader("Attach XML Exported File", type="xml")
    submitted = st.form_submit_button("Send Request")

    if submitted:
        st.session_state.last_user = user_email  # remember last user

        if not user_email or not serial or not uploaded_file:
            st.error("Please fill all fields and attach an XML file.")
        else:
            credits = st.session_state.credits.get(user_email, 0)
            if credits <= 0:
                st.error("❌ You have no credits. Please purchase credits first.")
            else:
                try:
                    file_name = uploaded_file.name
                    file_bytes = uploaded_file.read()
                    send_notification(user_email, serial, file_name, file_bytes)
                    # Deduct credit
                    st.session_state.credits[user_email] = credits - 1
                    st.success(f"✅ Request submitted successfully! Remaining credits: {st.session_state.credits[user_email]}")
                except Exception as e:
                    st.error(f"Failed to send request: {e}")
