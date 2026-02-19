import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from paypalrestsdk import Payment, configure
import json
from instamojo_wrapper import Instamojo  # OFFICIAL SDK!

# ---------------------------
# Streamlit page config
# ---------------------------
st.set_page_config(page_title="XML Key Generator", page_icon="🔒")

# ---------------------------
# Google Sheets setup (your existing code)
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
# OFFICIAL INSTAMOJO SDK (SIMPLE!)
# ---------------------------
@st.cache_resource
def get_instamojo_client():
    """Initialize official Instamojo SDK"""
    return Instamojo(
        api_key=st.secrets["instamojo"]["api_key"],
        auth_token=st.secrets["instamojo"]["auth_token"]
    )

def create_instamojo_payment(email: str, amount: int, credits: int):
    """Create payment using OFFICIAL SDK"""
    try:
        api = get_instamojo_client()
        
        response = api.payment_request_create(
            amount=str(amount),  # SDK expects string
            purpose=f"{credits} XML Key Credits",
            send_email=True,
            email=email,
            redirect_url=st.secrets.get("APP_URL", "https://your-app.streamlit.app")
        )
        
        if isinstance(response, dict) and response.get('payment_request'):
            return response['payment_request']['longurl']
        else:
            st.error(f"SDK Error: {response}")
            return None
    except Exception as e:
        st.error(f"Instamojo SDK error: {str(e)}")
        return None

# ---------------------------
# Your existing helper functions (unchanged)
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
# Buy Credits - OFFICIAL SDK + FALLBACKS
# ---------------------------
st.subheader("💳 Buy Credits")

tab1, tab2, tab3 = st.tabs(["🇮🇳 Instamojo SDK", "🇺🇸 PayPal", "📱 Manual (100% Working)"])

with tab1:
    st.markdown("**Official Instamojo Python SDK**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("**₹1700 - 1 Credit**", use_container_width=True, type="primary"):
            if email:
                with st.spinner("Creating via official SDK..."):
                    payment_url = create_instamojo_payment(email, 1700, 1)
                    if payment_url:
                        st.success("✅ **SDK Payment Ready!**")
                        st.markdown(f"[**Pay ₹1700**]({payment_url})")
                        st.balloons()
                    else:
                        st.info("🔗 **Manual:** https://www.instamojo.com/cctvindia")
            else:
                st.warning("Enter email!")
    
    with col2:
        if st.button("**₹8400 - 20 Credits**", use_container_width=True):
            if email:
                with st.spinner("Creating via official SDK..."):
                    payment_url = create_instamojo_payment(email, 8400, 20)
                    if payment_url:
                        st.success("✅ **SDK Payment Ready!**")
                        st.markdown(f"[**Pay ₹8400**]({payment_url})")
                        st.balloons()
                    else:
                        st.info("🔗 **Manual:** https://www.instamojo.com/cctvindia")
            else:
                st.warning("Enter email!")

with tab2:
    st.markdown("**PayPal for international clients**")
    credit_option = st.selectbox("Select USD pack", ["20 USD - 1 credit", "100 USD - 20 credits"])
    price, add_credits = (20, 1) if credit_option.startswith("20") else (100, 20)
    
    if st.button("💰 PayPal", use_container_width=True):
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
                "description": f"XML Tool Credits"
            }]
        })
        if payment.create():
            st.success("✅ PayPal ready!")
            for link in payment.links:
                if link.rel == "approval_url":
                    st.markdown(f"[**PayPal**]({link.href})")
        else:
            st.error("PayPal failed")

with tab3:
    st.success("**💯 Manual Links - Always Works!**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**[₹1700 - 1 Credit](https://www.instamojo.com/cctvindia)**")
    with col2:
        st.markdown("**[₹8400 - 20 Credits](https://www.instamojo.com/cctvindia)**")
    st.info("**Flow:** Client pays → Send screenshot → Credits added instantly!")

# ---------------------------
# Submit XML Request
# ---------------------------
st.subheader("📤 Submit XML Request")
if st.button("🚀 Send Request (1 Credit)", type="primary", use_container_width=True):
    if not all([email, serial, uploaded_file]):
        st.error("❌ Fill all fields + XML file")
    elif credits <= 0:
        st.error("❌ **No credits!** Buy above 👆")
        st.rerun()
    else:
        file_name = uploaded_file.name
        file_bytes = uploaded_file.read()
        send_notification(email, serial, file_name, file_bytes)
        deduct_user_credits(email, 1)
        st.success("🎉 **XML submitted!** Check email in 24h")
        st.balloons()

st.markdown("---")
st.caption("💡 Payments: Send screenshot to xmlkeyserver@gmail.com")
