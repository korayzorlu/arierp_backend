from partners.models import IncomeTypes

from decimal import Decimal

class FinancialProfileScore():
    def __init__(self, financial_profile):
        self.financial_profile = financial_profile
        self.financial_profile_socre = Decimal("0.00")
        self.gelir = Decimal("0.00")

    def calculate_gelir(self):
        if IncomeTypes.MAAS in self.financial_profile.income_types:
            self.gelir += Decimal("0.00") * Decimal("1.00")
        if IncomeTypes.KIRA in self.financial_profile.income_types:
            self.gelir += Decimal("0.00") * Decimal("1.00")
        if IncomeTypes.YATIRIM in self.financial_profile.income_types:
            self.gelir += Decimal("50.00") * Decimal("1.00")
        if IncomeTypes.TICARI in self.financial_profile.income_types:
            self.gelir += Decimal("50.00") * Decimal("1.00")
        if IncomeTypes.DIGER in self.financial_profile.income_types:
            self.gelir += Decimal("100.00") * Decimal("1.50")

    def calculate_financial_profile_score(self):
        self.calculate_gelir()
        self.financial_profile_socre += self.gelir
        return self.financial_profile_socre

def calculate_financial_profile_score(partner):
    gelir = Decimal("0.00")

    if partner.financial_profile:
        if partner.financial_profile.gelir:
            gelir = partner.financial_profile.gelir