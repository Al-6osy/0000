from datetime import datetime
from database import DatabaseManager

class EmployeeManager:
    def __init__(self, db, auth):
        self.db = db
        self.auth = auth
    
    def add_employee(self, emp_id, name, position, salary, bank_account):
        if not self.auth.has_permission('can_manage_employees'):
            print("ليس لديك صلاحية لإضافة موظفين!")
            return False
        
        encrypted_account = self.db.encrypt_data(bank_account)
        
        result = self.db.execute_query(
            '''INSERT INTO employees 
            (emp_id, name, position, salary, bank_account, current_balance, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (emp_id, name, position, salary, encrypted_account, salary, 
             self.auth.current_user['username'], str(datetime.now()))
        )
        
        if result is None:
            print("خطأ في إضافة الموظف!")
            return False
        
        print(f"تم إضافة الموظف {name} بنجاح!")
        return True
    
    def deduct_salary(self, emp_id, amount, reason):
        if not self.auth.has_permission('can_manage_finance'):
            print("ليس لديك صلاحية لاستقطاع الرواتب!")
            return False
        
        employee = self.db.execute_query(
            "SELECT name, current_balance FROM employees WHERE emp_id = ?",
            (emp_id,), fetchone=True
        )
        
        if not employee:
            print("رقم الموظف غير صحيح!")
            return False
        
        name, current_balance = employee
        
        if amount > current_balance:
            print("المبلغ المطلوب أكبر من الرصيد المتاح!")
            return False
        
        self.db.execute_query(
            "UPDATE employees SET current_balance = current_balance - ?, deductions = deductions + ? WHERE emp_id = ?",
            (amount, amount, emp_id)
        )
        
        print(f"تم استقطاع {amount} من راتب {name}. الرصيد المتبقي: {current_balance - amount}")
        return True
    
    def pay_salary(self, emp_id):
        if not self.auth.has_permission('can_manage_finance'):
            print("ليس لديك صلاحية لدفع الرواتب!")
            return False
        
        employee = self.db.execute_query(
            "SELECT name, salary FROM employees WHERE emp_id = ?",
            (emp_id,), fetchone=True
        )
        
        if not employee:
            print("رقم الموظف غير صحيح!")
            return False
        
        name, salary = employee
        
        self.db.execute_query(
            "UPDATE employees SET current_balance = ?, deductions = 0 WHERE emp_id = ?",
            (salary, emp_id)
        )
        
        print(f"تم دفع راتب {name} بالكامل. المبلغ: {salary}")
        return True