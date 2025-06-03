import hashlib
import getpass
from database import Database

class Auth:
    def __init__(self, db):
        self.db = db
        self.current_user = None
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self):
        username = input("اسم المستخدم: ")
        password = getpass.getpass("كلمة المرور: ")
        
        user = self.db.execute(
            "SELECT username, password, role FROM users WHERE username = ? AND is_active = 1",
            (username,)
        ).fetchone()
        
        if not user:
            print("اسم المستخدم أو كلمة المرور غير صحيحة!")
            return False
        
        if user[1] != self.hash_password(password):
            print("كلمة المرور غير صحيحة!")
            return False
        
        self.current_user = {
            'username': user[0],
            'role': user[2]
        }
        print(f"مرحباً {user[0]}! تم تسجيل الدخول بنجاح.")
        return True
    
    def logout(self):
        if self.current_user:
            print(f"تم تسجيل الخروج للمستخدم {self.current_user['username']}")
            self.current_user = None
    
    def is_authenticated(self):
        return self.current_user is not None
    
    def has_role(self, role):
        return self.is_authenticated() and self.current_user['role'] == role
