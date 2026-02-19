import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from paypalrestsdk import Payment, configure
import json
import requests  # NEW: For Instamojo API
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
    "mode": paypal_conf["mode"],  # live
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
# Instamojo Helper Function (NEW)
# ---------------------------
def create_instamojo_payment(email: str, amount: float, credits: int) -> Optional[str]:
    """Create Instamojo payment request"""
    try:
        url = "https://www.instamojo.com/api/1.1/payment-requests/"
        headers = {
            "X-Api-Key": st.secrets["instamojo"]["api_key"],
            "X-Auth-Token": st.secrets["instamojo"]["auth_token"],
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "purpose": f"{credits} XML Credits - Key Generator",
            "amount": f"{amount:.2f}",
            "email": email,
            "redirect_url": st.secrets.get("APP_URL", "https://your-app.streamlit.app"),
            "send_email": "true",
            "send_sms": "true",
            "allow_repeated_payments": "false"
        }
        
        response = requests.post(url, data=data, headers=headers, timeout=15)
        
        # Debug info (remove after testing)
        if st.checkbox("Show API Debug"):
            st.write(f"Status: {response.status_code}")
            st.write(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["payment_request"]["longurl"]
            else:
                st.error(f"API Error: {result.get('message', 'Unknown error')}")
        else:
            st.error(f"HTTP {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

# ---------------------------
# Helper functions
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
# Buy Credits - INSTAMOJO + PAYPAL
# ---------------------------
st.subheader("💳 Buy Credits")

# Indian pricing for Instamojo + USD for PayPal
credit_options = {
    "₹1700 - 1 credit (Instamojo)": (1700, 1),
    "₹8400 - 20 credits (Instamojo)": (8400, 20),
    "--- PayPal (USD) ---": (0, 0),
    "20 USD - 1 credit (PayPal)": (20, 1),
    "100 USD - 20 credits (PayPal)": (100, 20)
}

selected_option = st.selectbox("Select Credit Pack", list(credit_options.keys()))
price, add_credits = credit_options[selected_option]

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🇮🇳 Instamojo (INR)**")
    if "Instamojo" in selected_option and price > 0 and st.button("💳 Pay via Instamojo", use_container_width=True, type="primary"):
        if email:
            with st.spinner("Creating secure payment link..."):
                payment_url = create_instamojo_payment(email, price, add_credits)
                if payment_url:
                    st.success("✅ Payment link created successfully!")
                    st.balloons()
                    st.markdown(f"""
                    ## 👇 **Click to Pay Instantly:**
                    [**{selected_option}**]({payment_url})
                    """)
                    st.info(f"""
                    **✅ After payment:**
                    1. You'll get instant email confirmation
                    2. Check Instamojo dashboard
                    3. Reply with payment ID → Credits added instantly
                    4. Ready to generate XML keys!
                    """)
                else:
                    st.error("❌ Failed to create payment link. Try PayPal.")
        else:
            st.warning("⚠️ Please enter your email first")

with col2:
    st.markdown("**🇺🇸 PayPal (USD)**")
    if "PayPal" in selected_option and price > 0 and st.button("💰 Pay via PayPal", use_container_width=True):
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
                "description": f"Purchase {add_credits} credits for XML tool"
            }]
        })

        if payment.create():
            st.success("✅ PayPal payment created!")
            for link in payment.links:
                if link.rel == "approval_url":
                    st.markdown(f"[🔗 Complete Payment on PayPal]({link.href})")
        else:
            st.error("❌ PayPal setup error. Use Instamojo.")

# ---------------------------
# Submit XML Request
# ---------------------------
st.subheader("📤 Submit XML Request")

if st.button("🚀 Send XML Request", type="primary", use_container_width=True, help="1 credit will be deducted"):
    if not all([email, serial, uploaded_file]):
        st.error("❌ Please fill **all fields** and attach XML file.")
    elif credits <= 0:
        st.error("❌ **Insufficient credits**. Buy more using Instamojo/PayPal above!")
        st.info("💡 Credits auto-add after payment verification")
    else:
        file_name = uploaded_file.name
        file_bytes = uploaded_file.read()
        send_notification(email, serial, file_name, file_bytes)
        deduct_user_credits(email, 1)
        st.success("🎉 **Request submitted successfully!** 1 credit deducted.")
        st.balloons()
        st.balloons()

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.markdown("*Technical support: Reply with payment screenshot for instant credits*")


