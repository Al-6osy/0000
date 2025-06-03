import hashlib
import getpass
from datetime import datetime
from database import DatabaseManager

class AuthSystem:
    def __init__(self, db):
        self.db = db
        self.current_user = None
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self, username, password):
        user = self.db.execute_query(
            "SELECT username, password, role, is_active FROM users WHERE username = ?",
            (username,), fetchone=True
        )
        
        if not user:
            print("اسم المستخدم غير صحيح!")
            return False
        
        username_db, password_db, role, is_active = user
        
        if not is_active:
            print("الحساب معطل! يرجى التواصل مع المدير.")
            return False
        
        if password_db != self.hash_password(password):
            print("كلمة المرور غير صحيحة!")
            return False
        
        self.current_user = {
            'username': username_db,
            'role': role
        }
        
        self.db.execute_query(
            "UPDATE users SET last_login = ? WHERE username = ?",
            (str(datetime.now()), username_db)
        )
        
        print(f"مرحباً {username_db}! تم تسجيل الدخول بنجاح.")
        return True
    
    def logout(self):
        if self.current_user:
            print(f"تم تسجيل الخروج للمستخدم {self.current_user['username']}")
            self.current_user = None
    
    def has_permission(self, permission):
        if not self.current_user:
            return False
        
        result = self.db.execute_query(
            f"SELECT {permission} FROM permissions WHERE role = ?",
            (self.current_user['role'],), fetchone=True
        )
        
        return result and result[0] == 1
    
    def change_password(self, old_password, new_password):
        if not self.current_user:
            print("لا يوجد مستخدم مسجل!")
            return False
        
        user = self.db.execute_query(
            "SELECT password FROM users WHERE username = ?",
            (self.current_user['username'],), fetchone=True
        )
        
        if not user or user[0] != self.hash_password(old_password):
            print("كلمة المرور الحالية غير صحيحة!")
            return False
        
        self.db.execute_query(
            "UPDATE users SET password = ? WHERE username = ?",
            (self.hash_password(new_password), self.current_user['username'])
        )
        
        print("تم تغيير كلمة المرور بنجاح!")
        return True