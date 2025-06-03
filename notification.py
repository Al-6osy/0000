import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class EmailNotifier:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT'))
        self.sender_email = os.getenv('EMAIL_USERNAME')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        self.use_tls = os.getenv('USE_TLS', 'True').lower() == 'true'
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def send_email(self, recipient, subject, body):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            self.logger.info(f"تم إرسال البريد إلى {recipient}")
            return True
        except Exception as e:
            self.logger.error(f"فشل في إرسال البريد: {e}")
            return False