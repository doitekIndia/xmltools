import streamlit as st
import hashlib, base64, json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

# Load private key (server only, never share!)
with open("private_key.pem", "rb") as f:
    PRIVATE_KEY = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

def generate_key_xml(email: str, serial: str, xml: str) -> str:
    # 🔒 Replace this with your actual secret algorithm
    h = hashlib.sha256()
    h.update(email.encode())
    h.update(serial.encode())
    h.update(xml.encode())
    digest = h.hexdigest()
    return f'<?xml version="1.0" encoding="UTF-8"?><XMLKey><Email>{email}</Email><Serial>{serial}</Serial><Key>{digest}</Key></XMLKey>'

def sign_message(message: bytes) -> str:
    signature = PRIVATE_KEY.sign(
        message,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode()

st.set_page_config(page_title="🔑 Secure XML Key Generator", page_icon="🔒")

st.title("🔑 Secure XML Key Generator API (Streamlit)")

st.write("This page provides an **API endpoint**. The EXE client will call it securely.")

# --- API Simulation ---
st.subheader("Test API here (manual form)")

email = st.text_input("Email")
serial = st.text_input("Serial")
xml_input = st.text_area("XML content")

if st.button("Generate Key"):
    if not email or not serial or not xml_input:
        st.error("Please fill all fields.")
    else:
        key_xml = generate_key_xml(email, serial, xml_input)
        signature = sign_message(key_xml.encode())
        st.code(json.dumps({"key_xml": key_xml, "signature": signature}, indent=2), language="json")

# --- API Endpoint ---
# Clients can POST here: https://your-app.streamlit.app/?api=1
query_params = st.experimental_get_query_params()
if "api" in query_params:
    import sys
    body = sys.stdin.read()
    try:
        data = json.loads(body)
        key_xml = generate_key_xml(data["email"], data["serial"], data["xml"])
        sig = sign_message(key_xml.encode())
        print(json.dumps({"key_xml": key_xml, "signature": sig}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
