import os
from urllib.parse import unquote
import streamlit as st
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from paypalrestsdk import Payment, configure
import json

# ---------------------------
# Serve robots.txt / sitemap.xml
# ---------------------------
def _detect_request_path():
    """Try to detect the requested path. Best-effort."""
    candidates = []
    candidates.append(os.environ.get("PATH_INFO", ""))
    candidates.append(os.environ.get("REQUEST_URI", ""))
    candidates.append(os.environ.get("HTTP_X_ORIGINAL_URI", ""))
    candidates.append(os.environ.get("RAW_URI", ""))
    candidates.append(os.environ.get("URL", ""))
    candidates.append(os.environ.get("VIRTUAL_HOST", ""))

    try:
        qp = st.query_params
        qp_str = " ".join(
            [f"{k}={'|'.join(v) if isinstance(v, list) else v}" for k, v in qp.items()]
        )
        candidates.append(qp_str)
        if "_path" in qp:
            candidates.append(unquote(qp["_path"]))
    except Exception:
        pass

    return " ".join([str(c).lower() for c in candidates if c])


_request_path = _detect_request_path()

if "robots.txt" in _request_path:
    st.text("User-agent: *\nDisallow:\nSitemap: https://xmltools.streamlit.app/sitemap.xml")
    st.stop()

if "sitemap.xml" in _request_path:
    st.write("""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://xmltools.streamlit.app/</loc>
    <priority>1.0</priority>
  </url>
</urlset>
""")
    st.stop()


# ---------------------------
# Streamlit page config
# ---------------------------
st.set_page_config(
    page_title="XML Key Generator Tool | Free Online XML Tools",
    page_icon="🔒",
    layout="wide"
)

# ---------------------------
# Inject SEO + Google verification (head only, no blank space)
# ---------------------------
seo_html = """
<head>
<!-- Google Search Console -->
<meta name="google-site-verification" content="BiEq9uMceJh5Kae4u-bIk0-vNdQQtrDznK-3aI719vg" />

<!-- Basic meta -->
<meta name="description" content="Generate XML keys, manage device serials, and automate XML processing online. Secure and easy-to-use XML Key Generator with PayPal credits.">
<meta name="keywords" content="XML key generator, XML tools, online XML processing, XML file unlock, device serial XML, Hikvision XML, Dahua XML, IP camera XML reset">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://xmltools.streamlit.app/">

<!-- Open Graph / Facebook -->
<meta property="og:title" content="XML Key Generator Tool">
<meta property="og:description" content="Upload your XML file, manage credits, and generate XML keys instantly online.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://xmltools.streamlit.app/">
<meta property="og:image" content="https://xmltools.streamlit.app/static/xmltools-preview.png">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="XML Key Generator Tool">
<meta name="twitter:description" content="Free online XML tools to generate and process XML keys.">
<meta name="twitter:image" content="https://xmltools.streamlit.app/static/xmltools-preview.png">

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "XML Key Generator Tool",
    "url": "https://xmltools.streamlit.app/",
    "applicationCategory": "Utility",
    "operatingSystem": "All",
    "description": "Upload XML files, manage credits, and generate XML keys online securely.",
    "creator": {
        "@type": "Organization",
        "name": "XML Tools"
    }
}
</script>
</head>
"""
components.html(seo_html, height=0)

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
            try:
                return int(row[1])
            except Exception:
                return 0
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
st.markdown("""
### Free Online XML Tools
Upload your XML file, generate keys, and manage device serial numbers.  
Our **XML Key Generator** is built for security professionals, system admins, and CCTV/IP camera users.
""")

email = st.text_input("📧 Your Email ID")
serial = st.text_input("🔑 Device Serial Number")
uploaded_file = st.file_uploader("📂 Attach XML Exported File", type="xml")

credits = get_user_credits(email) if email else 0
st.write(f"💳 Your available credits: **{credits}**")

# ---------------------------
# PayPal payment
# ---------------------------
st.subheader("💰 Buy Credits")
credit_option = st.selectbox("Select Credit Pack", ["20 USD - 1 credit", "100 USD - 20 credits"])
price, add_credits = (20, 1) if credit_option.startswith("20") else (100, 20)

if st.button("Pay via PayPal"):
    payment = Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "https://xmltools.streamlit.app?success=true",
            "cancel_url": "https://xmltools.streamlit.app?cancel=true"
        },
        "transactions": [{
            "item_list": {"items": [{"name": f"{add_credits} Credits", "sku": "credits", "price": str(price), "currency": "USD", "quantity": 1}]},
            "amount": {"total": str(price), "currency": "USD"},
            "description": f"Purchase {add_credits} credits for XML tool"
        }]
    })

    if payment.create():
        st.success("✅ Payment created successfully. Please complete the payment on PayPal.")
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = str(link.href)
                st.markdown(f"[Click here to pay on PayPal]({approval_url})")
    else:
        st.error("❌ Payment creation failed. Check PayPal credentials.")

# ---------------------------
# Submit XML Request
# ---------------------------
if st.button("📨 Send XML Request"):
    if not email or not serial or not uploaded_file:
        st.error("⚠️ Please fill all fields and attach an XML file.")
    elif credits <= 0:
        st.error("⚠️ You have insufficient credits. Please purchase more credits.")
    else:
        file_name = uploaded_file.name
        file_bytes = uploaded_file.read()
        send_notification(email, serial, file_name, file_bytes)
        deduct_user_credits(email, 1)
        st.success("✅ Request submitted successfully! 1 credit deducted.")
