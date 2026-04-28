from django.test import TestCase
from communication.models import SMS
from companies.models import Company

class SMSModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Şirketi")

    def test_sms_creation(self):
        sms = SMS.objects.create(
            company=self.company,
            phone_number="5551234567",
            text="Test mesajı",
        )
        self.assertEqual(sms.status, '0')          # default değer
        self.assertIsNotNone(sms.uuid)
        self.assertEqual(str(sms), "5551234567 - Test mesajı")