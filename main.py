from database import DatabaseManager
from auth import AuthSystem
from employee_manager import EmployeeManager
from notification import EmailNotifier
import getpass
import os
from dotenv import load_dotenv
import pyfiglet

load_dotenv()

def display_menu(menu_items):
    print("\n" + "="*50)
    for i, item in enumerate(menu_items, 1):
        print(f"{i}. {item}")
    print("="*50)

def admin_menu(db, auth, emp_manager):
    while True:
        display_menu([
            "إضافة مستخدم جديد",
            "عرض جميع المستخدمين",
            "تعطيل/تفعيل مستخدم",
            "العودة للقائمة الرئيسية"
        ])
        
        choice = input("اختر الخيار: ")
        
        if choice == '1':
            username = input("اسم المستخدم: ")
            password = getpass.getpass("كلمة المرور: ")
            role = input("الصلاحية (admin/hr/finance/manager/employee): ")
            email = input("البريد الإلكتروني: ")
            
            db.execute_query(
                "INSERT INTO users (username, password, role, email, is_active) VALUES (?, ?, ?, ?, 1)",
                (username, auth.hash_password(password), role, email)
            )
            print("تم إضافة المستخدم بنجاح!")
        
        elif choice == '2':
            users = db.execute_query("SELECT username, role, email, is_active FROM users", fetchall=True)
            for user in users:
                status = "مفعل" if user[3] else "معطل"
                print(f"{user[0]} - {user[1]} - {user[2]} - {status}")
        
        elif choice == '3':
            username = input("اسم المستخدم: ")
            action = input("1. تعطيل\n2. تفعيل\nاختر الإجراء: ")
            
            if action == '1':
                db.execute_query("UPDATE users SET is_active = 0 WHERE username = ?", (username,))
                print("تم تعطيل الحساب")
            elif action == '2':
                db.execute_query("UPDATE users SET is_active = 1 WHERE username = ?", (username,))
                print("تم تفعيل الحساب")
        
        elif choice == '4':
            break

def hr_menu(db, auth, emp_manager):
    while True:
        display_menu([
            "إضافة موظف جديد",
            "عرض جميع الموظفين",
            "العودة للقائمة الرئيسية"
        ])
        
        choice = input("اختر الخيار: ")
        
        if choice == '1':
            emp_id = input("رقم الموظف: ")
            name = input("الاسم: ")
            position = input("الوظيفة: ")
            salary = float(input("الراتب: "))
            bank_account = input("الحساب البنكي: ")
            
            emp_manager.add_employee(emp_id, name, position, salary, bank_account)
        
        elif choice == '2':
            employees = db.execute_query(
                "SELECT emp_id, name, position, salary FROM employees", 
                fetchall=True
            )
            for emp in employees:
                print(f"{emp[0]} - {emp[1]} - {emp[2]} - {emp[3]}")
        
        elif choice == '3':
            break

def finance_menu(db, auth, emp_manager):
    while True:
        display_menu([
            "استقطاع من الراتب",
            "دفع الراتب",
            "العودة للقائمة الرئيسية"
        ])
        
        choice = input("اختر الخيار: ")
        
        if choice == '1':
            emp_id = input("رقم الموظف: ")
            amount = float(input("المبلغ: "))
            reason = input("السبب: ")
            emp_manager.deduct_salary(emp_id, amount, reason)
        
        elif choice == '2':
            emp_id = input("رقم الموظف: ")
            emp_manager.pay_salary(emp_id)
        
        elif choice == '3':
            break

def employee_menu(db, auth):
    while True:
        display_menu([
            "عرض معلوماتي",
            "تغيير كلمة المرور",
            "العودة للقائمة الرئيسية"
        ])
        
        choice = input("اختر الخيار: ")
        
        if choice == '1':
            emp_id = f"{auth.current_user['username']}_emp"
            employee = db.execute_query(
                "SELECT name, position, salary, current_balance FROM employees WHERE emp_id = ?",
                (emp_id,), fetchone=True
            )
            
            if employee:
                print(f"\nالاسم: {employee[0]}")
                print(f"الوظيفة: {employee[1]}")
                print(f"الراتب: {employee[2]}")
                print(f"الرصيد الحالي: {employee[3]}")
        
        elif choice == '2':
            old_pass = getpass.getpass("كلمة المرور الحالية: ")
            new_pass = getpass.getpass("كلمة المرور الجديدة: ")
            confirm_pass = getpass.getpass("تأكيد كلمة المرور: ")
            
            if new_pass == confirm_pass:
                auth.change_password(old_pass, new_pass)
            else:
                print("كلمة المرور غير متطابقة!")
        
        elif choice == '3':
            break

def main():
    db = DatabaseManager()
    auth = AuthSystem(db)
    emp_manager = EmployeeManager(db, auth)
    notifier = EmailNotifier()
    
    # إنشاء مستخدم مدير إذا لم يكن موجوداً
    if not db.execute_query("SELECT username FROM users WHERE role = 'admin'", fetchone=True):
        db.execute_query(
            "INSERT INTO users (username, password, role, is_active) VALUES (?, ?, ?, 1)",
            ('admin', auth.hash_password('admin123'), 'admin')
        )
        print("تم إنشاء مستخدم مدير افتراضي (admin/admin123)")
    
    while True:
        print(pyfiglet.figlet_format("Employee System"))
        
        if not auth.current_user:
            display_menu(["تسجيل الدخول", "خروج"])
            choice = input("اختر الخيار: ")
            
            if choice == '1':
                username = input("اسم المستخدم: ")
                password = getpass.getpass("كلمة المرور: ")
                auth.login(username, password)
            
            elif choice == '2':
                print("شكراً لاستخدامك النظام. إلى اللقاء!")
                break
        
        else:
            role = auth.current_user['role']
            
            if role == 'admin':
                admin_menu(db, auth, emp_manager)
            elif role == 'hr':
                hr_menu(db, auth, emp_manager)
            elif role == 'finance':
                finance_menu(db, auth, emp_manager)
            elif role == 'employee':
                employee_menu(db, auth)
            
            auth.logout()

if __name__ == "__main__":
    main()