notifier = NotificationSystem()
notifier.send_email(
    recipient="employee@example.com",
    subject="تم دفع راتبك",
    body="مرحباً محمد،\n\nتم دفع راتبك البالغ 5000 ريال.\n\nمع تحيات إدارة الشركة"
)