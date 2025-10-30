from django.test import TestCase

from .models import TrialBalance

# Create your tests here.

class TrialBalanceModelTests(TestCase):
    def setUp(self):
        # Create some TrialBalance objects for testing
        TrialBalance.objects.create(account_code="996.013.4.00.003")
        TrialBalance.objects.create(account_code="250.03.0.011")

    def test_trial_balance_object_count(self):
        """
        Test that the number of TrialBalance objects is correct.
        """
        count = TrialBalance.objects.count()
        self.assertEqual(count, 2)