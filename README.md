# XML Key Generator 🔒

A Streamlit-based web application for submitting XML files, managing user credits, and processing payments via PayPal.

## 🚀 Features
- Upload XML files securely
- Credit-based usage system
- PayPal payment integration
- Google Sheets used as lightweight database
- Email notifications with XML attachments

## 🧩 How It Works
1. User enters email and device serial number
2. User uploads an XML file
3. Credits are checked before submission
4. One credit is deducted per request
5. XML file is emailed to the service inbox

## 🔐 Security & Credentials
This project requires private credentials that are **NOT included** in this repository:
- Google Service Account (Sheets API)
- PayPal Client ID & Secret
- Email SMTP credentials

All secrets must be stored using **Streamlit Secrets** or environment variables.

## ⚠️ Important Notice
Anyone deploying this project must:
- Use **their own** PayPal account
- Use **their own** Google Sheet and service account
- Use **their own** email credentials

This repository does **NOT** provide access to any paid service, credits, or infrastructure.

## 📄 License
See the LICENSE file for usage terms.
