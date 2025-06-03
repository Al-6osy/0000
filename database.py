import sqlite3
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('employees.db')
        self.cipher = Fernet(os.getenv('ENCRYPTION_KEY').encode())
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT,
            last_login TEXT,
            failed_attempts INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
        ''')
        
        # جدول الموظفين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            salary REAL NOT NULL,
            bank_account TEXT NOT NULL,
            current_balance REAL NOT NULL,
            deductions REAL DEFAULT 0,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
        ''')
        
        # جدول الصلاحيات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            role TEXT PRIMARY KEY,
            can_manage_employees INTEGER DEFAULT 0,
            can_manage_finance INTEGER DEFAULT 0,
            can_view_reports INTEGER DEFAULT 0
        )
        ''')
        
        # إدراج الصلاحيات الافتراضية
        cursor.executemany('''
        INSERT OR IGNORE INTO permissions (role, can_manage_employees, can_manage_finance, can_view_reports)
        VALUES (?, ?, ?, ?)
        ''', [
            ('admin', 1, 1, 1),
            ('hr', 1, 0, 1),
            ('finance', 0, 1, 1),
            ('manager', 1, 0, 0),
            ('employee', 0, 0, 0)
        ])
        
        self.conn.commit()
    
    def encrypt_data(self, data):
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def execute_query(self, query, params=(), fetchone=False, fetchall=False):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
            if fetchone:
                result = cursor.fetchone()
            elif fetchall:
                result = cursor.fetchall()
            else:
                result = None
            
            self.conn.commit()
            return result
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {e}")
            return None
    
    def close(self):
        self.conn.close()