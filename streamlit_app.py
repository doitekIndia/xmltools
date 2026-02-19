import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from paypalrestsdk import Payment, configure
import json
import requests
from typing import Optional

# ---------------------------
# Streamlit page config
# ---------------------------
st.set_page_config(page_title="XML Key Generator", page_icon="🔒")

# ---------------------------
# Google Sheets setup
# ---------------------------
service_account_info = json.loads(st.secrets["gdrive"]["service_account_json"])
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
client = gspread.authorize(creds)
SPREADSHEET_ID = "1H2mj-rzVGwgU09E90dW6YUjhTuaYJo2LBJrMsnJVErg"
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# ---------------------------
# PayPal configuration
# ---------------------------
paypal_conf = st.secrets["paypal"]
configure({
    "mode": paypal_conf["mode"],
    "client_id": paypal_conf["client_id"],
    "client_secret": paypal_conf["client_secret"]
})

# ---------------------------
# Email setup
# ---------------------------
EMAIL_FROM = st.secrets["email"]["user"]
EMAIL_PASSWORD = st.secrets["email"]["app_password"]
EMAIL_TO = "xmlkeyserver@gmail.com"

# ---------------------------
# FIXED Instamojo Function (LIVE MODE)
# ---------------------------
def create_instamojo_payment(email: str, amount: float, credits: int) -> Optional[str]:
    """Create Instamojo LIVE payment request"""
    try:
        url = "https://www.instamojo.com/api/1.1/payment-requests/"  # LIVE
        headers = {
            "X-Api-Key": st.secrets["instamojo"]["api_key"],
            "X-Auth-Token": st.secrets["instamojo"]["auth_token"],
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "purpose": f"{credits} XML Credits - Key Generator",
            "amount": str(int(amount)),  # Integer only!
            "email": email,
            "redirect_url": st.secrets.get("APP_URL", "https://your-app.streamlit.app"),
            "send_email": "true",
            "send_sms": "true",
            "allow_repeated_payments": "false"
        }
        
        response = requests.post(url, data=data, headers=headers, timeout=15)
        
        if st.checkbox("🔧 Debug API Response"):
            st.json({"status": response.status_code, "response": response.text[:500]})
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["payment_request"]["longurl"]
            st.error(f"API Error: {result.get('message', result)}")
        elif response.status_code == 403:
            st.error("🔒 **Instamojo API 403** - Account needs API activation")
            st.info("👉 Use manual link below (100% working!)")
        else:
            st.error(f"HTTP {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

# ---------------------------
# Helper functions (unchanged)
# ---------------------------
def send_notification(user_email, serial, file_name, file_bytes):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "New XML Key Request"
    body = f"Email: {user_email}\nSerial: {serial}\nFile: {file_name}"
    msg.attach(MIMEText(body, "plain"))
    attachment = MIMEApplication(file_bytes, _subtype="xml")
    attachment.add_header("Content-Disposition", "attachment", filename=file_name)
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

def get_user_credits(email):
    all_values = sheet.get_all_values()
    for row in all_values[1:]:
        if row[0] == email:
            return int(row[1])
    return 0

def update_user_credits(email, added_credits):
    all_values = sheet.get_all_values()
    for i, row in enumerate(all_values[1:], start=2):
        if row[0] == email:
            new_credits = int(row[1]) + added_credits
            sheet.update(f"B{i}", new_credits)
            return new_credits
    sheet.append_row([email, added_credits])
    return added_credits

def deduct_user_credits(email, used_credits):
    all_values = sheet.get_all_values()
    for i, row in enumerate(all_values[1:], start=2):
        if row[0] == email:
            new_credits = int(row[1]) - used_credits
            sheet.update(f"B{i}", new_credits)
            return new_credits
    return 0

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("🔒 XML Key Generator Tool")
st.write("Upload your XML file and manage credits.")

email = st.text_input("📧 Your Email ID")
serial = st.text_input("🔢 Device Serial Number")
uploaded_file = st.file_uploader("📎 Attach XML Exported File", type="xml")
credits = get_user_credits(email) if email else 0
st.markdown(f"**💰 Your available credits: {credits}**")

# ---------------------------
# Buy Credits - MULTIPLE OPTIONS (PRODUCTION READY)
# ---------------------------
st.subheader("💳 Buy Credits")

tab1, tab2, tab3 = st.tabs(["🇮🇳 Instamojo", "🇺🇸 PayPal", "📱 Manual Links"])

with tab1:
    st.markdown("**Fastest for Indian clients**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("**₹1700 - 1 Credit**", use_container_width=True):
            if email:
                payment_url = create_instamojo_payment(email, 1700, 1)
                if payment_url:
                    st.success("✅ **Payment Ready!**")
                    st.markdown(f"[**Pay ₹1700 Now**]({payment_url})")
                else:
                    st.info("🔗 **Manual:** https://www.instamojo.com/cctvindia")
            else:
                st.warning("Enter email first")
    
    with col2:
        if st.button("**₹8400 - 20 Credits**", use_container_width=True):
            if email:
                payment_url = create_instamojo_payment(email, 8400, 20)
                if payment_url:
                    st.success("✅ **Payment Ready!**")
                    st.markdown(f"[**Pay ₹8400 Now**]({payment_url})")
                else:
                    st.info("🔗 **Manual:** https://www.instamojo.com/cctvindia")
            else:
                st.warning("Enter email first")

with tab2:
    st.markdown("**International clients**")
    credit_option = st.selectbox("USD Pack", ["20 USD - 1 credit", "100 USD - 20 credits"])
    price, add_credits = (20, 1) if credit_option.startswith("20") else (100, 20)
    
    if st.button("💰 Pay via PayPal", use_container_width=True):
        payment = Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": st.secrets.get("APP_URL", "https://your-app.streamlit.app") + "?success=true",
                "cancel_url": st.secrets.get("APP_URL", "https://your-app.streamlit.app") + "?cancel=true"
            },
            "transactions": [{
                "item_list": {"items": [{"name": f"{add_credits} Credits", "sku": "credits", "price": str(price), "currency": "USD", "quantity": 1}]},
                "amount": {"total": str(price), "currency": "USD"},
                "description": f"XML Tool - {add_credits} credits"
            }]
        })

        if payment.create():
            st.success("✅ PayPal Ready!")
            for link in payment.links:
                if link.rel == "approval_url":
                    st.markdown(f"[**Complete on PayPal**]({link.href})")
        else:
            st.error("❌ PayPal failed")

with tab3:
    st.markdown("**💯 100% Working - Share with clients**")
    st.info("🔗 **Instamojo:** https://www.instamojo.com/cctvindia")
    st.info("📱 **WhatsApp:** Send clients this link")
    st.code("https://wa.me/+91YOURNUMBER?text=XML%20Credits:%20https://www.instamojo.com/cctvindia")
    st.success("**Flow:** Client pays → Screenshot → You add credits instantly!")

# ---------------------------
# Submit XML Request
# ---------------------------
st.subheader("📤 Submit XML Request")
if st.button("🚀 Send XML Request", type="primary", use_container_width=True):
    if not all([email, serial, uploaded_file]):
        st.error("❌ Fill all fields + attach XML")
    elif credits <= 0:
        st.error("❌ No credits! Buy above 👆")
        st.info("💡 Send payment screenshot for instant credits")
    else:
        file_name = uploaded_file.name
        file_bytes = uploaded_file.read()
        send_notification(email, serial, file_name, file_bytes)
        deduct_user_credits(email, 1)
        st.success("🎉 XML sent! 1 credit deducted. Reply coming in 24h")
        st.balloons()

st.markdown("---")
st.markdown("*Send payment screenshot to: xmlkeyserver@gmail.com*")
