import streamlit as st
import smtplib
import gspread
from google.oauth2.service_account import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json

st.set_page_config(page_title="XML Key Generator Tool - Testing", page_icon="🔑")

# -------------------------------
# Email setup
EMAIL_USER = st.secrets["email"]["user"]
EMAIL_PASSWORD = st.secrets["email"]["app_password"]
EMAIL_TO = "xmlkeyserver@gmail.com"

# -------------------------------
# Google Sheets setup
gdrive_json = json.loads(st.secrets["gdrive"]["service_account_json"])
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(gdrive_json, scopes=SCOPE)
client = gspread.authorize(creds)

CREDITS_SHEET = client.open("XML_Credits_DB").sheet1
try:
    REQUESTS_SHEET = client.open("XML_Requests_DB").sheet1
except:
    # create new sheet if not exists
    sh = client.create("XML_Requests_DB")
    REQUESTS_SHEET = sh.sheet1
    REQUESTS_SHEET.append_row(["Email", "Serial", "File Name", "Status"])

# -------------------------------
# Helper functions
def get_credits(email):
    data = CREDITS_SHEET.get_all_records()
    for row in data:
        if row["Email"].strip().lower() == email.strip().lower():
            return int(row["Credits"])
    return 0

def update_credits(email, new_credits):
    data = CREDITS_SHEET.get_all_records()
    row_num = None
    for idx, row in enumerate(data, start=2):
        if row["Email"].strip().lower() == email.strip().lower():
            row_num = idx
            break
    if row_num:
        CREDITS_SHEET.update_cell(row_num, 2, new_credits)
    else:
        CREDITS_SHEET.append_row([email, new_credits])

def add_request(email, serial, file_name, status="Pending"):
    REQUESTS_SHEET.append_row([email, serial, file_name, status])

# -------------------------------
# Email sending
def send_notification(user_email, serial, file_name, file_bytes):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = "New XML Key Request (Testing)"

    body = f"New XML key request:\n\nEmail: {user_email}\nSerial: {serial}\nFile: {file_name}"
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(file_bytes, _subtype="xml")
    attachment.add_header("Content-Disposition", "attachment", filename=file_name)
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)

# -------------------------------
# UI

st.title("🔑 XML Key Generator Tool - Testing Mode")

# Buy credits (simulate)
st.header("💳 Add Credits for Testing")
email_for_purchase = st.text_input("Your Email for Testing")

if st.button("✅ Add 1 Credit (Temp)"):
    if email_for_purchase:
        current = get_credits(email_for_purchase)
        update_credits(email_for_purchase, current + 1)
        st.success(f"Added 1 credit. Total: {current + 1}")
    else:
        st.error("Enter your email")

if st.button("✅ Add 20 Credits (Temp)"):
    if email_for_purchase:
        current = get_credits(email_for_purchase)
        update_credits(email_for_purchase, current + 20)
        st.success(f"Added 20 credits. Total: {current + 20}")
    else:
        st.error("Enter your email")

# Submit XML
st.header("📤 Submit XML Request for Testing")
with st.form("xml_form", clear_on_submit=True):
    user_email = st.text_input("Your Email ID")
    serial = st.text_input("Device Full Serial Number")
    uploaded_file = st.file_uploader("Attach XML Exported File", type="xml")
    submitted = st.form_submit_button("Send Request")

    if submitted:
        if not user_email or not serial or not uploaded_file:
            st.error("⚠️ Fill all fields and upload file")
        else:
            credits = get_credits(user_email)
            if credits <= 0:
                st.error("❌ You have no credits. Add credits first.")
            else:
                try:
                    # Send email
                    send_notification(user_email, serial, uploaded_file.name, uploaded_file.read())
                    # Reduce credit
                    update_credits(user_email, credits - 1)
                    # Log request
                    add_request(user_email, serial, uploaded_file.name, status="Sent")
                    st.success(f"✅ Request sent! Remaining credits: {credits - 1}")
                except Exception as e:
                    st.error(f"Failed: {e}")
