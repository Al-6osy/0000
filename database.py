import sqlite3
import logging
from cryptography.fernet import Fernet, InvalidToken
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_NAME)
        self.cursor = self.conn.cursor()
        self.cipher = Fernet(Config.ENCRYPTION_KEY.encode())
        self._create_tables()
    
    def _create_tables(self):
        try:
            # جدول المستخدمين
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                is_active INTEGER DEFAULT 1
            )
            ''')
            
            # جدول الموظفين
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                salary REAL NOT NULL,
                bank_account TEXT NOT NULL,
                balance REAL NOT NULL,
                created_by TEXT,
                FOREIGN KEY (created_by) REFERENCES users(username)
            )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"خطأ في إنشاء الجداول: {e}")
    
    def encrypt(self, data):
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"خطأ في التشفير: {e}")
            return None
    
    def decrypt(self, encrypted_data):
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except InvalidToken:
            logger.error("مفتاح التشفير غير صحيح!")
            return None
        except Exception as e:
            logger.error(f"خطأ في فك التشفير: {e}")
            return None
    
    def execute(self, query, params=(), commit=False):
        try:
            result = self.cursor.execute(query, params)
            if commit:
                self.conn.commit()
            return result
        except sqlite3.Error as e:
            logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
            return None
    
    def close(self):
        self.conn.close()
