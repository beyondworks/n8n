import os
import sys
import json
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_config():
    """Load config from notion_config.json"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'notion_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def send_email_notification(subject, body, recipient=None):
    config = load_config()

    # Get SMTP credentials from config or env
    smtp_user = config.get("smtp_user") or os.environ.get("SMTP_USER")
    smtp_pass = config.get("smtp_password") or os.environ.get("SMTP_PASSWORD")

    if not recipient:
        recipient = smtp_user  # Send to self by default

    if not smtp_user or not smtp_pass:
        print("⚠️ Email Skipped: Missing SMTP credentials in config or environment.")
        print("   Add 'smtp_user' and 'smtp_password' to notion_config.json")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {recipient}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

if __name__ == "__main__":
    # Test or CLI usage
    if len(sys.argv) >= 3:
        subj = sys.argv[1]
        body = sys.argv[2]
        send_email_notification(subj, body)
    else:
        # Quick test
        send_email_notification("🧪 Test Email", "Content Repurposing 스킬에서 보낸 테스트 메일입니다.")

