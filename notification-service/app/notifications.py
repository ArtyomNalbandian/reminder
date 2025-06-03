import firebase_admin
from firebase_admin import credentials, messaging
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import ssl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
cred_path = os.getenv("FCM_CREDENTIALS_FILE")
if cred_path and os.path.exists(cred_path):
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
else:
    logger.error(f"Firebase credentials file not found at {cred_path}")

# SMTP configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.yandex.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Log SMTP configuration (without password)
logger.info(f"SMTP Configuration - Host: {SMTP_HOST}, Port: {SMTP_PORT}, Username: {SMTP_USERNAME}")

async def send_fcm_notification(token: str, title: str, body: str) -> bool:
    try:
        logger.info(f"Attempting to send FCM notification - Title: {title}, Body: {body}, Token: {token[:20]}...")
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=token
        )
        response = messaging.send(message)
        logger.info(f"FCM notification sent successfully. Message ID: {response}")
        return True
    except Exception as e:
        logger.error(f"Error sending FCM notification: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full error details: {e}")
        return False

async def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    try:
        logger.info(f"Attempting to send email notification to {to_email}")
        
        if not all([SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
            logger.error("Missing SMTP configuration")
            return False

        message = MIMEMultipart()
        message["From"] = SMTP_USERNAME
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        # Create SSL context
        ssl_context = ssl.create_default_context()
        
        logger.info(f"Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT}")
        async with aiosmtplib.SMTP(hostname=SMTP_HOST, 
                                 port=SMTP_PORT,
                                 use_tls=True,
                                 tls_context=ssl_context) as smtp:
            
            logger.info("Attempting SMTP login")
            await smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            logger.info("SMTP login successful, sending message")
            
            await smtp.send_message(message)
            logger.info(f"Email sent successfully to {to_email}")
        return True
    except aiosmtplib.SMTPException as e:
        logger.error(f"SMTP Error sending email: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full error details: {e}")
        return False 