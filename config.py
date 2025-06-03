import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # إعدادات قاعدة البيانات
    DB_NAME = "employees.db"
    
    # إعدادات البريد الإلكتروني
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    
    # مفتاح التشفير (يتم توليده إذا لم يوجد)
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default_encryption_key_here')
