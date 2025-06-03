from datetime import datetime
from database import Database

class EmployeeManager:
    def __init__(self, db, auth):
        self.db = db
        self.auth = auth
    
    def add_employee(self):
        if not self.auth.is_authenticated():
            print("يجب تسجيل الدخول أولاً!")
            return False
        
        emp_id = input("رقم الموظف: ")
        name = input("الاسم الكامل: ")
        position = input("الوظيفة: ")
        salary = float(input("الراتب: "))
        bank_account = input("رقم الحساب البنكي: ")
        
        encrypted_account = self.db.encrypt(bank_account)
        if not encrypted_account:
            print("حدث خطأ في تشفير البيانات!")
            return False
        
        self.db.execute(
            '''INSERT INTO employees 
            (id, name, position, salary, bank_account, balance, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (emp_id, name, position, salary, encrypted_account, salary, self.auth.current_user['username']),
            commit=True
        )
        
        print(f"تم إضافة الموظف {name} بنجاح!")
        return True
    
    def list_employees(self):
        employees = self.db.execute(
            "SELECT id, name, position, salary, balance FROM employees"
        ).fetchall()
        
        if not employees:
            print("لا يوجد موظفين مسجلين!")
            return
        
        print("\nقائمة الموظفين:")
        for emp in employees:
            print(f"{emp[0]} - {emp[1]} - {emp[2]} - الراتب: {emp[3]} - الرصيد: {emp[4]}")
    
    def process_salary(self, emp_id, amount, is_deduction=False):
        employee = self.db.execute(
            "SELECT name, balance FROM employees WHERE id = ?",
            (emp_id,)
        ).fetchone()
        
        if not employee:
            print("رقم الموظف غير صحيح!")
            return False
        
        name, balance = employee
        new_balance = balance - amount if is_deduction else balance + amount
        
        if is_deduction and new_balance < 0:
            print("لا يمكن استقطاع هذا المبلغ! الرصيد غير كافي.")
            return False
        
        self.db.execute(
            "UPDATE employees SET balance = ? WHERE id = ?",
            (new_balance, emp_id),
            commit=True
        )
        
        action = "استقطاع" if is_deduction else "دفع"
        print(f"تم {action} مبلغ {amount} للموظف {name}. الرصيد الجديد: {new_balance}")
        return True
