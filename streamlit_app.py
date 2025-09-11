# backend_flask.py

from flask import Flask, request, jsonify
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

app = Flask(__name__)

EMAIL_FROM = "hikvisionxml@gmail.com"
EMAIL_TO = "xmlkeyserver@gmail.com"
EMAIL_PASSWORD = os.environ.get("EMAIL_PASS")  # Store securely, or use .env

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

@app.route("/api/xmlkey", methods=["POST"])
def api_xmlkey():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data sent"}), 400
        user_email = data.get("email")
        serial = data.get("serial")
        file_name = data.get("file_name")
        file_content = data.get("file_content")  # base64 encoded
        if not all([user_email, serial, file_name, file_content]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        file_bytes = base64.b64decode(file_content)
        send_notification(user_email, serial, file_name, file_bytes)
        return jsonify({"status": "success", "message": "Request submitted and email sent."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(port=8501)
