import smtplib, ssl
from django.core.mail.backends.smtp import EmailBackend

class CustomEmailBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False
        self.connection = smtplib.SMTP(self.host, self.port)
        self.connection.ehlo()
        self.connection.starttls(context=ssl._create_unverified_context())  # doğrulama atlanıyor
        self.connection.ehlo()
        if self.username and self.password:
            self.connection.login(self.username, self.password)
        return True