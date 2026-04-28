import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from communication.models import SMS
from companies.models import Company, UserCompany
from common.models import Currency
from users.models import User


class SMSModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Şirketi")

    def test_sms_creation(self):
        sms = SMS.objects.create(
            company=self.company,
            phone_number="5551234567",
            text="Test mesajı",
        )
        self.assertEqual(sms.status, '0')
        self.assertIsNotNone(sms.uuid)
        self.assertEqual(str(sms), "5551234567 - Test mesajı")


class SendRiskEmailViewTest(TestCase):
    def setUp(self):
        self.currency = Currency.objects.create(code="TRY", name="Türk Lirası")
        self.company = Company.objects.create(name="Test Şirketi")

        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user.authorization.department = "kredi_risk_izleme"
        self.user.authorization.save()
        self.user_company = UserCompany.objects.create(
            user=self.user,
            company=self.company,
            display_currency=self.currency,
        )

        self.unauthorized_user = User.objects.create_user(username="otheruser", password="testpass")
        self.unauthorized_user.authorization.department = "finans"
        self.unauthorized_user.authorization.save()
        UserCompany.objects.create(
            user=self.unauthorized_user,
            company=self.company,
            display_currency=self.currency,
        )

        self.url = reverse("send_risk_email")
        self.payload = json.dumps({
            "ac": str(self.user_company.uuid),
            "risk_status": "risk",
        })

    def test_unauthorized_department_returns_403(self):
        self.client.force_login(self.unauthorized_user)
        response = self.client.post(
            self.url, data=self.payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["status"], "error")

    @patch("communication.views.email_views.send_email_with_setrow_task")
    def test_authorized_user_triggers_task_and_returns_200(self, mock_task):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url, data=self.payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        mock_task.delay.assert_called_once()

    @patch("communication.views.email_views.send_email_with_setrow_task")
    def test_task_called_with_correct_user_and_company(self, mock_task):
        self.client.force_login(self.user)
        self.client.post(self.url, data=self.payload, content_type="application/json")

        call_args = mock_task.delay.call_args[0][0]
        self.assertEqual(call_args["user_id"], str(self.user.uuid))
        self.assertEqual(call_args["company_id"], str(self.company.uuid))