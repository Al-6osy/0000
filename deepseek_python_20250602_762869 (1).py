import json
import os
import hashlib
import getpass
from datetime import datetime
import sqlite3
import smtplib
from email.mime.text import MIMEText

import secrets
import string



# إعداد قاعدة البيانات
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('employee_management.db')
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
            reset_token TEXT,
            token_expiry TEXT,
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
        
        # جدول سجل الاستقطاعات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS deductions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            amount REAL NOT NULL,
            reason TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
        ''')
        
        # جدول سجل المدفوعات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            amount REAL NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
            FOREIGN KEY (created_by) REFERENCES users(username)
        )
        ''')
        
        # جدول الصلاحيات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            role TEXT PRIMARY KEY,
            can_add_employee INTEGER DEFAULT 0,
            can_deduct_salary INTEGER DEFAULT 0,
            can_pay_salary INTEGER DEFAULT 0,
            can_view_all_employees INTEGER DEFAULT 0,
            can_manage_users INTEGER DEFAULT 0
        )
        ''')
        
        # إدخال الصلاحيات الافتراضية
        cursor.execute('''
        INSERT OR IGNORE INTO permissions (role, can_add_employee, can_deduct_salary, can_pay_salary, can_view_all_employees, can_manage_users)
        VALUES 
            ('admin', 1, 1, 1, 1, 1),
            ('hr_manager', 1, 1, 1, 1, 0),
            ('finance_manager', 0, 1, 1, 1, 0),
            ('department_manager', 1, 0, 0, 1, 0),
            ('employee', 0, 0, 0, 0, 0)
        ''')
        
        self.conn.commit()
    
    def execute_query(self, query, params=(), fetchone=False, fetchall=False):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        self.conn.commit()
        return result
    
    def close(self):
        self.conn.close()

# نظام الإشعارات
class NotificationSystem:
    def __init__(self):
        self.smtp_server = "smtp.example.com"
        self.smtp_port = 587
        self.sender_email = "system@company.com"
        self.sender_password = "email_password"
    
    def send_email(self, recipient, subject, body):
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"فشل في إرسال البريد: {e}")
            return False

# نظام المصادقة
class AuthenticationSystem:
    def __init__(self, db_manager, notification_system):
        self.db = db_manager
        self.notifier = notification_system
        self.current_user = None
        self.login_attempts = 0
        self.max_attempts = 5
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_reset_token(self):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def register(self, username, password, email, role='employee'):
        if self.db.execute_query("SELECT username FROM users WHERE username = ?", (username,), fetchone):
            print("اسم المستخدم موجود بالفعل!")
            return False
        
        hashed_pw = self.hash_password(password)
        self.db.execute_query(
            "INSERT INTO users (username, password, role, email, last_login) VALUES (?, ?, ?, ?, ?)",
            (username, hashed_pw, role, email, None)
        )
        
        # إرسال إشعار الترحيب
        subject = "حسابك الجديد في نظام إدارة الموظفين"
        body = f"مرحباً {username},\n\nتم إنشاء حسابك بنجاح في نظام إدارة الموظفين.\n\nصلاحيتك: {role}\n\nيمكنك تسجيل الدخول الآن."
        self.notifier.send_email(email, subject, body)
        
        print(f"تم تسجيل المستخدم {username} بنجاح!")
        return True
    
    def login(self, username, password):
        if self.login_attempts >= self.max_attempts:
            print("تم تجاوز عدد المحاولات المسموح بها! النظام مغلق مؤقتاً.")
            return False
        
        user = self.db.execute_query(
            "SELECT username, password, role, failed_attempts, is_active FROM users WHERE username = ?",
            (username,), fetchone
        )
        
        if not user:
            print("اسم المستخدم أو كلمة المرور غير صحيحة!")
            self.login_attempts += 1
            return False
        
        username_db, password_db, role, failed_attempts, is_active = user
        
        if not is_active:
            print("الحساب معطل! يرجى التواصل مع المدير.")
            return False
        
        if failed_attempts >= 3:
            print("الحساب مؤقتاً بسبب كثرة المحاولات الفاشلة!")
            return False
        
        if password_db != self.hash_password(password):
            self.db.execute_query(
                "UPDATE users SET failed_attempts = failed_attempts + 1 WHERE username = ?",
                (username,)
            )
            print("اسم المستخدم أو كلمة المرور غير صحيحة!")
            self.login_attempts += 1
            return False
        
        self.current_user = {
            'username': username,
            'role': role
        }
        
        self.db.execute_query(
            "UPDATE users SET last_login = ?, failed_attempts = 0 WHERE username = ?",
            (str(datetime.now)), username)
        
        self.login_attempts = 0
        print(f"مرحباً {username}! تم تسجيل الدخول بنجاح.")
        return True
    
    def logout(self):
        if self.current_user:
            print(f"تم تسجيل الخروج للمستخدم {self.current_user['username']}")
            self.current_user = None
        else:
            print("لا يوجد مستخدم مسجل حالياً!")
    
    def has_permission(self, permission_name):
        if not self.current_user:
            return False
        
        role = self.current_user['role']
        query = f"SELECT {permission_name} FROM permissions WHERE role = ?"
        result = self.db.execute_query(query, (role,), fetchone)
        
        return result and result[0] == 1
    
    def request_password_reset(self, email):
        user = self.db.execute_query(
            "SELECT username FROM users WHERE email = ?",
            (email,), fetchone
        )
        
        if not user:
            print("لا يوجد حساب مرتبط بهذا البريد الإلكتروني!")
            return False
        
        username = user[0]
        token = self.generate_reset_token()
        expiry = datetime.now() + timedelta(hours=1)
        
        self.db.execute_query(
            "UPDATE users SET reset_token = ?, token_expiry = ? WHERE username = ?",
            (token, str(expiry), username)
        )
        
        reset_link = f"https://yourapp.com/reset-password?token={token}"
        subject = "إعادة تعيين كلمة المرور"
        body = f"مرحباً {username},\n\nلإعادة تعيين كلمة المرور، يرجى النقر على الرابط التالي:\n{reset_link}\n\nالرابط صالح لمدة ساعة واحدة."
        
        if self.notifier.send_email(email, subject, body):
            print("تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني.")
            return True
        else:
            print("فشل في إرسال رابط إعادة التعيين.")
            return False
    
    def reset_password(self, token, new_password):
        user = self.db.execute_query(
            "SELECT username, token_expiry FROM users WHERE reset_token = ?",
            (token,), fetchone
        )
        
        if not user:
            print("رابط إعادة التعيين غير صالح!")
            return False
        
        username, expiry_str = user
        expiry = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S.%f')
        
        if datetime.now() > expiry:
            print("انتهت صلاحية رابط إعادة التعيين!")
            return False
        
        hashed_pw = self.hash_password(new_password)
        self.db.execute_query(
            "UPDATE users SET password = ?, reset_token = NULL, token_expiry = NULL WHERE username = ?",
            (hashed_pw, username)
        )
        
        print("تم إعادة تعيين كلمة المرور بنجاح!")
        return True

# نظام إدارة الموظفين
class EmployeeManager:
    def __init__(self, db_manager, auth_system, notifier):
        self.db = db_manager
        self.auth = auth_system
        self.notifier = notifier
    
    def add_employee(self, emp_id, name, position, salary, bank_account):
        if not self.auth.has_permission('can_add_employee'):
            print("ليس لديك صلاحية لإضافة موظفين!")
            return False
        
        if self.db.execute_query("SELECT emp_id FROM employees WHERE emp_id = ?", (emp_id,), fetchone):
            print("موظف بهذا الرقم موجود بالفعل!")
            return False
        
        encrypted_account = encrypt_data(bank_account)
        
        self.db.execute_query(
            '''INSERT INTO employees 
            (emp_id, name, position, salary, bank_account, current_balance, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (emp_id, name, position, salary, encrypted_account, salary, 
             self.auth.current_user['username'], str(datetime.now)))
        
        # إرسال إشعار للموظف الجديد
        user_email = self.db.execute_query(
            "SELECT email FROM users WHERE username = ?",
            (f"{emp_id}_user",), fetchone
        )
        
        if user_email:
            subject = "تمت إضافتك إلى نظام الموظفين"
            body = f"مرحباً {name},\n\nتمت إضافتك إلى نظام إدارة الموظفين.\n\nالوظيفة: {position}\nالراتب: {salary}"
            self.notifier.send_email(user_email[0], subject, body)
        
        print(f"تم إضافة الموظف {name} بنجاح!")
        return True
    
    def list_employees(self):
        if not self.auth.has_permission('can_view_all_employees'):
            print("ليس لديك صلاحية لعرض قائمة الموظفين!")
            return
        
        employees = self.db.execute_query(
            "SELECT emp_id, name, position, salary, current_balance FROM employees",
            fetchall=True
        )
        
        if not employees:
            print("لا يوجد موظفين مسجلين!")
            return
        
        print("\nقائمة الموظفين:")
        for emp in employees:
            print(f"ID: {emp[0]} | الاسم: {emp[1]} | الوظيفة: {emp[2]} | الراتب: {emp[3]} | الرصيد الحالي: {emp[4]}")
    
    def deduct_from_salary(self, emp_id, amount, reason):
        if not self.auth.has_permission('can_deduct_salary'):
            print("ليس لديك صلاحية لاستقطاع من الرواتب!")
            return False
        
        employee = self.db.execute_query(
            "SELECT name, current_balance FROM employees WHERE emp_id = ?",
            (emp_id,), fetchone
        )
        
        if not employee:
            print("رقم الموظف غير صحيح!")
            return False
        
        name, current_balance = employee
        if amount > current_balance:
            print("المبلغ المطلوب استقطاعه أكبر من الرصيد المتاح!")
            return False
        
        new_balance = current_balance - amount
        
        # تحديث رصيد الموظف
        self.db.execute_query(
            "UPDATE employees SET current_balance = ?, deductions = deductions + ? WHERE emp_id = ?",
            (new_balance, amount, emp_id)
        )
        
        # تسجيل عملية الاستقطاع
        self.db.execute_query(
            '''INSERT INTO deductions 
            (emp_id, amount, reason, created_by, created_at)
            VALUES (?, ?, ?, ?, ?)''',
            (emp_id, amount, reason, self.auth.current_user['username'], str(datetime.now)))
        
        # إرسال إشعار للموظف
        user_email = self.db.execute_query(
            "SELECT email FROM users WHERE username = ?",
            (f"{emp_id}_user",), fetchone
        )
        
        if user_email:
            subject = "تم استقطاع من راتبك"
            body = f"مرحباً {name},\n\nتم استقطاع مبلغ {amount} من راتبك.\nالسبب: {reason}\n\nالرصيد الحالي: {new_balance}"
            self.notifier.send_email(user_email[0], subject, body)
        
        print(f"تم استقطاع {amount} من راتب الموظف {name}. الرصيد المتبقي: {new_balance}")
        return True
    
    def pay_salary(self, emp_id):
        if not self.auth.has_permission('can_pay_salary'):
            print("ليس لديك صلاحية لدفع الرواتب!")
            return False
        
        employee = self.db.execute_query(
            "SELECT name, salary FROM employees WHERE emp_id = ?",
            (emp_id,), fetchone
        )
        
        if not employee:
            print("رقم الموظف غير صحيح!")
            return False
        
        name, salary = employee
        
        # تحديث رصيد الموظف
        self.db.execute_query(
            "UPDATE employees SET current_balance = ?, deductions = 0 WHERE emp_id = ?",
            (salary, emp_id)
        )
        
        # تسجيل عملية الدفع
        self.db.execute_query(
            '''INSERT INTO payments 
            (emp_id, amount, created_by, created_at)
            VALUES (?, ?, ?, ?)''',
            (emp_id, salary, self.auth.current_user['username'], str(datetime.now)))
        
        # إرسال إشعار للموظف
        user_email = self.db.execute_query(
            "SELECT email FROM users WHERE username = ?",
            (f"{emp_id}_user",), fetchone
        )
        
        if user_email:
            subject = "تم دفع راتبك"
            body = f"مرحباً {name},\n\nتم دفع راتبك بالكامل.\n\nالمبلغ: {salary}"
            self.notifier.send_email(user_email[0], subject, body)
        
        print(f"تم دفع راتب الموظف {name} بالكامل. المبلغ: {salary}")
        return True
    
    def get_employee_info(self, emp_id):
        # الموظف العادي يمكنه فقط رؤية معلوماته الخاصة
        if (self.auth.current_user['role'] == 'employee' and 
            not emp_id.startswith(self.auth.current_user['username'])):
            print("ليس لديك صلاحية لعرض معلومات هذا الموظف!")
            return None
        
        employee = self.db.execute_query(
            "SELECT * FROM employees WHERE emp_id = ?",
            (emp_id,), fetchone
        )
        
        if not employee:
            print("رقم الموظف غير صحيح!")
            return None
        
        # فك تشفير الحساب البنكي
        decrypted_account = decrypt_data(employee[4])
        
        emp_info = {
            'emp_id': employee[0],
            'name': employee[1],
            'position': employee[2],
            'salary': employee[3],
            'bank_account': decrypted_account,
            'current_balance': employee[5],
            'deductions': employee[6],
            'created_by': employee[7],
            'created_at': employee[8]
        }
        
        # الحصول على سجل الاستقطاعات
        deductions = self.db.execute_query(
            "SELECT amount, reason, created_by, created_at FROM deductions WHERE emp_id = ? ORDER BY created_at DESC",
            (emp_id,), fetchall=True
        )
        
        if deductions:
            emp_info['deduction_history'] = []
            for ded in deductions:
                emp_info['deduction_history'].append({
                    'amount': ded[0],
                    'reason': ded[1],
                    'by': ded[2],
                    'at': ded[3]
                })
        
        # الحصول على سجل المدفوعات
        payments = self.db.execute_query(
            "SELECT amount, created_by, created_at FROM payments WHERE emp_id = ? ORDER BY created_at DESC",
            (emp_id,), fetchall=True
        )
        
        if payments:
            emp_info['payment_history'] = []
            for pay in payments:
                emp_info['payment_history'].append({
                    'amount': pay[0],
                    'by': pay[1],
                    'at': pay[2]
                })
        
        return emp_info

# الواجهات المختلفة
def admin_menu(db, auth, emp_manager):
    while True:
        print("\nلوحة المدير العام:")
        print("1. إضافة مستخدم جديد")
        print("2. عرض جميع المستخدمين")
        print("3. تعطيل/تفعيل حساب مستخدم")
        print("4. إدارة الصلاحيات")
        print("5. العودة للقائمة الرئيسية")
        
        choice = input("اختر الخيار: ")
        
        if choice == '1':
            username = input("ادخل اسم المستخدم الجديد: ")
            password = getpass.getpass("ادخل كلمة المرور: ")
            email = input("ادخل البريد الإلكتروني: ")
            role = input("ادخل الصلاحية (admin/hr_manager/finance_manager/department_manager/employee): ")
            auth.register(username, password, email, role)
        
        elif choice == '2':
            users = db.execute_query("SELECT username, role, email, last_login, is_active FROM users", fetchall=True)
            print("\nقائمة المستخدمين:")
            for user in users:
                status = "مفعل" if user[4] else "معطل"
                print(f"المستخدم: {user[0]} | الصلاحية: {user[1]} | البريد: {user[2]} | آخر دخول: {user[3]} | الحالة: {status}")
        
        elif choice == '3':
            username = input("ادخل اسم المستخدم: ")
            action = input("1. تعطيل الحساب\n2. تفعيل الحساب\nاختر الإجراء: ")
            
            if action == '1':
                db.execute_query("UPDATE users SET is_active = 0 WHERE username = ?", (username,))
                print("تم تعطيل الحساب بنجاح!")
            elif action == '2':
                db.execute_query("UPDATE users SET is_active = 1, failed_attempts = 0 WHERE username = ?", (username,))
                print("تم تفعيل الحساب بنجاح!")
        
        elif choice == '4':
            role = input("ادخل الصلاحية التي تريد تعديلها: ")
            permissions = db.execute_query(
                "SELECT can_add_employee, can_deduct_salary, can_pay_salary, can_view_all_employees, can_manage_users FROM permissions WHERE role = ?",
                (role,), fetchone
            )
            
            if not permissions:
                print("الصلاحية غير موجودة!")
                continue
            
            print(f"\nصلاحيات {role} الحالية:")
            print(f"1. إضافة موظفين: {'نعم' if permissions[0] else 'لا'}")
            print(f"2. استقطاع من الرواتب: {'نعم' if permissions[1] else 'لا'}")
            print(f"3. دفع الرواتب: {'نعم' if permissions[2] else 'لا'}")
            print(f"4. عرض جميع الموظفين: {'نعم' if permissions[3] else 'لا'}")
            print(f"5. إدارة المستخدمين: {'نعم' if permissions[4] else 'لا'}")
            
            perm_choice = input("اختر رقم الصلاحية لتعديلها (أو اتركه فارغاً للعودة): ")
            
            if perm_choice in ['1', '2', '3', '4', '5']:
                column = [
                    'can_add_employee',
                    'can_deduct_salary',
                    'can_pay_salary',
                    'can_view_all_employees',
                    'can_manage_users'
                ][int(perm_choice)-1]
                
                new_value = not permissions[int(perm_choice)-1]
                db.execute_query
                    
            
                
                print(f"تم تحديث صلاحية {column} إلى {'نعم' if new_value else 'لا'}")
        
        elif choice == '5':
            break
        
        else:
            print("اختيار غير صحيح!")

def hr_manager_menu(db, auth, emp_manager):
    while True:
        print("\nلوحة مدير الموارد البشرية:")
        print("1. إضافة موظف جديد")
        print("2. عرض قائمة الموظفين")
        print("3. عرض معلومات موظف")
        print("4. العودة للقائمة الرئيسية")
        
        choice = input("اختر الخيار: ")
        
        if choice == '1':
            emp_id = input("ادخل رقم الموظف: ")
            name = input("ادخل اسم الموظف: ")
            position = input("ادخل الوظيفة: ")
            salary = float(input("ادخل الراتب: "))
            bank_account = input("ادخل رقم الحساب البنكي: ")
            emp_manager.add_employee(emp_id, name, position, salary, bank_account)
        
        elif choice == '2':
            emp_manager.list_employees()
        
        elif choice == '3':
            emp_id = input("ادخل رقم الموظف: ")
            emp_info = emp_manager.get_employee_info(emp_id)
            if emp_info:
                print("\nمعلومات الموظف:")
                print(f"الاسم: {emp_info['name']}")
                print(f"الوظيفة: {emp_info['position']}")
                print(f"الراتب: {emp_info['salary']}")
                print(f"الرصيد الحالي: {emp_info['current_balance']}")
                print(f"إجمالي الاستقطاعات: {emp_info['deductions']}")
        
        elif choice == '4':
            break
        
        else:
            print("اختيار غير صحيح!")

def finance_manager_menu(db, auth, emp_manager):
    while True:
        print("\nلوحة مدير المالية:")
        print("1. استقطاع من راتب موظف")
        print("2. دفع راتب موظف")
        print("3. عرض سجل الاستقطاعات")
        print("4. عرض سجل المدفوعات")
        print("5. العودة للقائمة الرئيسية")
        
        choice = input("اختر الخيار: ")
        
        if choice == '1':
            emp_id = input("ادخل رقم الموظف: ")
            amount = float(input("ادخل المبلغ المراد استقطاعه: "))
            reason = input("ادخل سبب الاستقطاع: ")
            emp_manager.deduct_from_salary(emp_id, amount, reason)
        
        elif choice == '2':
            emp_id = input("ادخل رقم الموظف: ")
            emp_manager.pay_salary(emp_id)
        
        elif choice == '3':
            emp_id = input("ادخل رقم الموظف: ")
            deductions = db.execute_query(
                "SELECT amount, reason, created_by, created_at FROM deductions WHERE emp_id = ? ORDER BY created_at DESC",
                (emp_id,), fetchall=True
            )
            
            if deductions:
                print("\nسجل الاستقطاعات:")
                for ded in deductions:
                    print(f"المبلغ: {ded[0]} | السبب: {ded[1]} | بواسطة: {ded[2]} | في: {ded[3]}")
            else:
                print("لا يوجد استقطاعات مسجلة لهذا الموظف.")
        
        elif choice == '4':
            emp_id = input("ادخل رقم الموظف: ")
            payments = db.execute_query(
                "SELECT amount, created_by, created_at FROM payments WHERE emp_id = ? ORDER BY created_at DESC",
                (emp_id,), fetchall=True
            )
            
            if payments:
                print("\nسجل المدفوعات:")
                for pay in payments:
                    print(f"المبلغ: {pay[0]} | بواسطة: {pay[1]} | في: {pay[2]}")
            else:
                print("لا يوجد مدفوعات مسجلة لهذا الموظف.")
        
        elif choice == '5':
            break
        
        else:
            print("اختيار غير صحيح!")

def employee_menu(db, auth, emp_manager):
    emp_id = f"{auth.current_user['username']}_emp"
    
    while True:
        print("\nلوحة الموظف:")
        print("1. عرض معلوماتي")
        print("2. تغيير كلمة المرور")
        print("3. العودة للقائمة الرئيسية")
        
        choice = input("اختر الخيار: ")
        
        if choice == '1':
            emp_info = emp_manager.get_employee_info(emp_id)
            if emp_info:
                print("\nمعلومات الموظف:")
                print(f"الاسم: {emp_info['name']}")
                print(f"الوظيفة: {emp_info['position']}")
                print(f"الراتب: {emp_info['salary']}")
                print(f"الرصيد الحالي: {emp_info['current_balance']}")
                print(f"إجمالي الاستقطاعات: {emp_info['deductions']}")
                
                if 'deduction_history' in emp_info:
                    print("\nسجل الاستقطاعات:")
                    for ded in emp_info['deduction_history']:
                        print(f"المبلغ: {ded['amount']} | السبب: {ded['reason']} | بواسطة: {ded['by']} | في: {ded['at']}")
        
        elif choice == '2':
            old_password = getpass.getpass("ادخل كلمة المرور الحالية: ")
            new_password = getpass.getpass("ادخل كلمة المرور الجديدة: ")
            confirm_password = getpass.getpass("أعد إدخال كلمة المرور الجديدة: ")
            
            if new_password != confirm_password:
                print("كلمة المرور الجديدة غير متطابقة!")
                continue
            
            # التحقق من كلمة المرور الحالية
            user = db.execute_query(
                "SELECT password FROM users WHERE username = ?",
                (auth.current_user['username'],), fetchone
            )
            
            if user and user[0] == auth.hash_password(old_password):
                hashed_pw = auth.hash_password(new_password)
                db.execute_query(
                    "UPDATE users SET password = ? WHERE username = ?",
                    (hashed_pw, auth.current_user['username'])
                )
                print("تم تغيير كلمة المرور بنجاح!")
            else:
                print("كلمة المرور الحالية غير صحيحة!")
        
        elif choice == '3':
            break
        
        else:
            print("اختيار غير صحيح!")

def main():
    db = DatabaseManager()
    notifier = NotificationSystem()
    auth = AuthenticationSystem(db, notifier)
    emp_manager = EmployeeManager(db, auth, notifier)
    
    # إنشاء مستخدم مدير افتراضي إذا لم يكن موجوداً


    
    while True:
        if not auth.current_user:
            print("\nنظام إدارة الموظفين - تسجيل الدخول")
            print("1. تسجيل الدخول")
            print("2. استعادة كلمة المرور")
            print("3. الخروج من النظام")
            
            choice = input("اختر الخيار: ")
            
            if choice == '1':
                username = input("اسم المستخدم: ")
                password = getpass.getpass("كلمة المرور: ")
                auth.login(username, password)
            
            elif choice == '2':
                email = input("ادخل البريد الإلكتروني المرتبط بحسابك: ")
                auth.request_password_reset(email)
            
            elif choice == '3':
                print("شكراً لاستخدامك النظام. إلى اللقاء!")
                break
            
            else:
                print("اختيار غير صحيح!")
        else:
            if auth.current_user['role'] == 'admin':
                admin_menu(db, auth, emp_manager)
            elif auth.current_user['role'] == 'hr_manager':
                hr_manager_menu(db, auth, emp_manager)
            elif auth.current_user['role'] == 'finance_manager':
                finance_manager_menu(db, auth, emp_manager)
            elif auth.current_user['role'] == 'employee':
                employee_menu(db, auth, emp_manager)
            else:
                print("صلاحيتك غير معروفة!")
            
            # تسجيل الخروج بعد إنهاء المهام
            auth.logout()

if __name__ == "__main__":
    main()