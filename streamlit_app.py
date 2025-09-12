import streamlit as st
import smtplib
import paypalrestsdk
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

st.set_page_config(page_title="XML Key Generator Tool", page_icon="🔑")

# -------------------------------
# Email config (from secrets)
EMAIL_USER = st.secrets["email"]["user"]
EMAIL_PASSWORD = st.secrets["email"]["app_password"]
EMAIL_TO = "xmlkeyserver@gmail.com"

# PayPal config
paypalrestsdk.configure({
    "mode": st.secrets["paypal"]["mode"],  # "sandbox" or "live"
    "client_id": st.secrets["paypal"]["client_id"],
    "client_secret": st.secrets["paypal"]["client_secret"]
})

# -------------------------------
# Session state for credits
if "credits" not in st.session_state:
    st.session_state.credits = {}
if "pending_payment" not in st.session_state:
    st.session_state.pending_payment = None

# -------------------------------
# Email function
def send_notification(user_email, serial, file_name, file_bytes):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = "New XML Key Request"

    body = f"New XML key request:\n\nEmail: {user_email}\nSerial: {serial}\nFile: {file_name}"
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(file_bytes, _subtype="xml")
    attachment.add_header("Content-Disposition", "attachment", filename=file_name)
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)

# -------------------------------
# Buy credits (PayPal)
def buy_credits(user_email, amount, credits):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://localhost:8501",  # Streamlit dev URL (use app URL on cloud)
            "cancel_url": "http://localhost:8501"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": f"{credits} XML Credits",
                    "sku": "xml-credits",
                    "price": str(amount),
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {"total": str(amount), "currency": "USD"},
            "description": f"Purchase of {credits} credits for {user_email}"
        }]
    })

    if payment.create():
        st.session_state.pending_payment = {
            "user": user_email,
            "credits": credits,
            "payment_id": payment.id
        }
        for link in payment.links:
            if link.rel == "approval_url":
                st.markdown(f"👉 [Pay Now via PayPal]({link.href})", unsafe_allow_html=True)
                return
    else:
        st.error("❌ Payment creation failed.")

# -------------------------------
# UI
st.title("🔑 XML Key Generator Tool (Credit Based)")

# Section 1: Buy credits
st.header("💳 Buy Credits")
email_for_purchase = st.text_input("Your Email for credits")

col1, col2 = st.columns(2)
with col1:
    if st.button("Buy 1 Credit ($20)"):
        if email_for_purchase:
            buy_credits(email_for_purchase, 20, 1)
        else:
            st.error("Enter your email first.")

with col2:
    if st.button("Buy 20 Credits ($100)"):
        if email_for_purchase:
            buy_credits(email_for_purchase, 100, 20)
        else:
            st.error("Enter your email first.")

# Simulate capture (normally webhook needed)
if st.session_state.pending_payment:
    if st.button("✅ Confirm Payment (Simulated)"):
        p = st.session_state.pending_payment
        st.session_state.credits[p["user"]] = st.session_state.credits.get(p["user"], 0) + p["credits"]
        st.success(f"✅ Added {p['credits']} credits to {p['user']}.")
        st.session_state.pending_payment = None

# Section 2: Submit request
st.header("📤 Submit XML Request")
with st.form("xml_form", clear_on_submit=True):
    user_email = st.text_input("Your Email ID")
    serial = st.text_input("Device Full Serial Number")
    uploaded_file = st.file_uploader("Attach XML Exported File", type="xml")
    submitted = st.form_submit_button("Send Request")

    if submitted:
        if not user_email or not serial or not uploaded_file:
            st.error("⚠️ Fill all fields and upload file.")
        else:
            credits = st.session_state.credits.get(user_email, 0)
            if credits <= 0:
                st.error("❌ You have no credits. Buy credits first.")
            else:
                try:
                    send_notification(user_email, serial, uploaded_file.name, uploaded_file.read())
                    st.session_state.credits[user_email] -= 1
                    st.success(f"✅ Request sent! Remaining credits: {st.session_state.credits[user_email]}")
                except Exception as e:
                    st.error(f"Failed: {e}")
