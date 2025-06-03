import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import os
from dotenv import load_dotenv
import logging

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

class NotificationSystem:
    def __init__(self):
        # إعدادات خادم البريد (يتم قراءتها من ملف .env أو المتغيرات البيئية)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('EMAIL_USERNAME', 'your.email@example.com')
        self.sender_password = os.getenv('EMAIL_PASSWORD', 'your-email-password')
        self.use_ssl = os.getenv('USE_SSL', 'False').lower() == 'true'
        self.use_tls = os.getenv('USE_TLS', 'True').lower() == 'true'
        
        # إعداد نظام التسجيل (logging)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # التحقق من صحة الإعدادات
        self._validate_settings()
    
    def _validate_settings(self):
        """التحقق من صحة إعدادات البريد الإلكتروني"""
        required_settings = {
            'SMTP_SERVER': self.smtp_server,
            'EMAIL_USERNAME': self.sender_email,
            'EMAIL_PASSWORD': self.sender_password
        }
        
        for name, value in required_settings.items():
            if not value:
                self.logger.error(f'إعدادات البريد الإلكتروني غير مكتملة: {name} غير معرّف')
                raise ValueError(f'الرجاء تعيين {name} في ملف .env أو المتغيرات البيئية')
    
    def send_email(self, recipient, subject, body, html_body=None):
        """
        إرسال بريد إلكتروني
        
        :param recipient: عنوان البريد الإلكتروني للمستلم
        :param subject: موضوع البريد
        :param body: نص البريد (نسخة نصية)
        :param html_body: نص البريد (نسخة HTML) - اختياري
        :return: True إذا تم الإرسال بنجاح، False إذا فشل
        """
        try:
            # إنشاء رسالة البريد
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient
            
            # إضافة محتوى البريد (نصي وHTML إذا متوفر)
            part1 = MIMEText(body, 'plain')
            msg.attach(part1)
            
            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)
            
            # إنشاء اتصال آمن مع خادم البريد
            context = ssl.create_default_context()
            
            if self.use_ssl:
                # استخدام اتصال SSL (على المنفذ 465 عادة)
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
            else:
                # استخدام اتصال عادي مع STARTTLS (على المنفذ 587 عادة)
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.use_tls:
                        server.starttls(context=context)
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
            
            self.logger.info(f'تم إرسال البريد إلى {recipient} بنجاح')
            return True
        except smtplib.SMTPAuthenticationError:
            self.logger.error('فشل المصادقة مع خادم البريد. الرجاء التحقق من اسم المستخدم وكلمة المرور.')
        except smtplib.SMTPException as e:
            self.logger.error(f'حدث خطأ في إرسال البريد: {str(e)}')
        except Exception as e:
            self.logger.error(f'حدث خطأ غير متوقع: {str(e)}')
        
        return False

    def send_template_email(self, recipient, subject, template_name, template_vars={}):
        """
        إرسال بريد إلكتروني باستخدام قالب
        
        :param recipient: عنوان البريد الإلكتروني للمستلم
        :param subject: موضوع البريد
        :param template_name: اسم ملف القالب (بدون امتداد)
        :param template_vars: متغيرات القالب
        :return: True إذا تم الإرسال بنجاح، False إذا فشل
        """
        try:
            # قراءة القالب النصي
            with open(f'templates/{template_name}.txt', 'r', encoding='utf-8') as f:
                text_template = f.read()
            
            # قراءة القالب HTML إذا كان موجوداً
            html_template = None
            try:
                with open(f'templates/{template_name}.html', 'r', encoding='utf-8') as f:
                    html_template = f.read()
            except FileNotFoundError:
                pass
            
            # استبدال المتغيرات في القوالب
            text_body = text_template.format(**template_vars)
            html_body = html_template.format(**template_vars) if html_template else None
            
            return self.send_email(recipient, subject, text_body, html_body)
        except FileNotFoundError:
            self.logger.error(f'ملف القالب {template_name} غير موجود')
            return False
        except Exception as e:
            self.logger.error(f'حدث خطأ في معالجة القالب: {str(e)}')
            return False