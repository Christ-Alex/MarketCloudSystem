# utils.py
import bcrypt
import random
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
load_dotenv()


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_otp() -> str:
    """Generate a random 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_otp(to_email: str, otp: str) -> bool:
    """Send OTP via Gmail SMTP using environment variables."""
    from_email = os.getenv("GMAIL_SENDER")      # e.g. your Gmail address
    from_password = os.getenv("GMAIL_APP_PWD")  # your Gmail app password

    if not from_email or not from_password:
        raise RuntimeError("Set GMAIL_SENDER and GMAIL_APP_PWD environment variables")

    subject = "Your OTP Code for the Cloud Security Simulator"
    body = f"Your OTP code is: {otp}\nThis code expires in 5 minutes."

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(from_email, from_password)
            server.send_message(msg)
            print(f"OTP sent to {to_email}")
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False