from database import Database
from auth import Auth
from employee import EmployeeManager

def display_menu(options):
    print("\n" + "="*40)
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    print("="*40)

def admin_menu(db, auth, emp_manager):
    while True:
        display_menu([
            "إضافة موظف جديد",
            "عرض الموظفين",
            "تسجيل الخروج"
        ])
        
        choice = input("اختر الخيار: ")
        
        if choice == '1':
            emp_manager.add_employee()
        elif choice == '2':
            emp_manager.list_employees()
        elif choice == '3':
            auth.logout()
            break
        else:
            print("اختيار غير صحيح!")

def main():
    db = Database()
    auth = Auth(db)
    emp_manager = EmployeeManager(db, auth)
    
    # إنشاء مستخدم مدير إذا لم يكن موجوداً
    if not db.execute("SELECT username FROM users WHERE role = 'admin'").fetchone():
        db.execute(
            "INSERT INTO users (username, password, role, is_active) VALUES (?, ?, ?, 1)",
            ('admin', auth.hash_password('admin123'), 'admin'),
            commit=True
        )
        print("تم إنشاء مستخدم مدير افتراضي (admin/admin123)")
    
    while True:
        if not auth.is_authenticated():
            display_menu(["تسجيل الدخول", "خروج"])
            choice = input("اختر الخيار: ")
            
            if choice == '1':
                auth.login()
            elif choice == '2':
                print("شكراً لاستخدامك النظام!")
                break
            else:
                print("اختيار غير صحيح!")
        else:
            if auth.has_role('admin'):
                admin_menu(db, auth, emp_manager)
            else:
                print("ليس لديك صلاحية الدخول إلى هذه الواجهة!")
                auth.logout()
