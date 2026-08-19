from partners.models import IncomeTypes,FundSource,RiskStatus,ComplianceStatus,AmountTRY,Frequency

from decimal import Decimal

class CalcPartnerScore():
    def __init__(self, financial_profile=None, partner_score=None):
        self.financial_profile = financial_profile
        self.partner_score = partner_score
        self.mr_score = Decimal("0.00")
        self.mr_weight = Decimal("0.00")

    def calc_gelir(self):
        if IncomeTypes.MAAS in self.financial_profile.income_types:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if IncomeTypes.TICARI in self.financial_profile.income_types:
            self.mr_score += Decimal("50.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if IncomeTypes.KIRA in self.financial_profile.income_types:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if IncomeTypes.YATIRIM in self.financial_profile.income_types:
            self.mr_score += Decimal("50.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if IncomeTypes.KRIPTO in self.financial_profile.income_types:
            self.mr_score += Decimal("100.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if IncomeTypes.BELIRSIZ in self.financial_profile.income_types:
            self.mr_score += Decimal("100.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if IncomeTypes.YOK in self.financial_profile.income_types:
            self.mr_score += Decimal("100.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if IncomeTypes.DIGER in self.financial_profile.income_types:
            self.mr_score += Decimal("100.00") * Decimal("1.50")
            self.mr_weight += Decimal("1.50")

    def calc_fon(self):
        if FundSource.SATIS in self.financial_profile.fund_sources:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if FundSource.TICARI in self.financial_profile.fund_sources:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if FundSource.MAAS in self.financial_profile.fund_sources:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if FundSource.MAAS_BIRIKIMI in self.financial_profile.fund_sources:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if FundSource.KIRA in self.financial_profile.fund_sources:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if FundSource.MIRAS in self.financial_profile.fund_sources:
            self.mr_score += Decimal("50.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if FundSource.SIRKET in self.financial_profile.fund_sources:
            self.mr_score += Decimal("50.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if FundSource.YURTDISI in self.financial_profile.fund_sources:
            self.mr_score += Decimal("100.00") * Decimal("1.50")
            self.mr_weight += Decimal("1.50")
        if FundSource.BELIRSIZ in self.financial_profile.fund_sources:
            self.mr_score += Decimal("100.00") * Decimal("2.00")
            self.mr_weight += Decimal("2.00")
        if FundSource.KRIPTO in self.financial_profile.fund_sources:
            self.mr_score += Decimal("100.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if FundSource.YOK in self.financial_profile.fund_sources:
            self.mr_score += Decimal("100.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        if FundSource.DIGER in self.financial_profile.fund_sources:
            self.mr_score += Decimal("100.00") * Decimal("2.00")
            self.mr_weight += Decimal("2.00")

    def calc_islem_davranisi(self):
        if self.financial_profile.transaction_amount == AmountTRY.RANGE_0:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        elif self.financial_profile.transaction_amount == AmountTRY.RANGE_0_100K:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        elif self.financial_profile.transaction_amount == AmountTRY.RANGE_100K_500K:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        elif self.financial_profile.transaction_amount == AmountTRY.RANGE_500K_2M:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        elif self.financial_profile.transaction_amount == AmountTRY.RANGE_2M_10M:
            self.mr_score += Decimal("50.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        elif self.financial_profile.transaction_amount == AmountTRY.RANGE_10M_ABOVE:
            self.mr_score += Decimal("100.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")

        if self.financial_profile.transaction_frequency == Frequency._0_2:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        elif self.financial_profile.transaction_frequency == Frequency._3_4:
            self.mr_score += Decimal("50.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        elif self.financial_profile.transaction_frequency == Frequency._5_ABOVE:
            self.mr_score += Decimal("100.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")

        if self.financial_profile.transaction_risk == RiskStatus.RISKLI_DEGIL:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        elif self.financial_profile.transaction_risk == RiskStatus.RISKLI:
            self.mr_score += Decimal("100.00") * Decimal("2.00")
            self.mr_weight += Decimal("2.00")

        if self.financial_profile.job_compliance == ComplianceStatus.UYUMLU:
            self.mr_score += Decimal("0.00") * Decimal("1.00")
            self.mr_weight += Decimal("1.00")
        elif self.financial_profile.job_compliance == ComplianceStatus.UYUMLU_DEGIL:
            self.mr_score += Decimal("100.00") * Decimal("1.50")
            self.mr_weight += Decimal("1.50")

    def calc_mr(self):
        # ort = top(w*x)/top(w)
        self.calc_gelir()
        self.calc_fon()
        self.calc_islem_davranisi()
        # self.partner_score.mr_score = self.mr_score / self.mr_weight if self.mr_weight > Decimal("0.00") else Decimal("0.00")
        return self.mr_score / self.mr_weight if self.mr_weight > Decimal("0.00") else Decimal("0.00")

    def calc_score(self):
        # skor = (mr*0.30)+(ühr*0.25)+(cgr*0.20)+(ödk*0.15)+(ilh*0.10)
        return (self.calc_mr()*Decimal("1.00"))

def calculate_financial_profile_score(partner):
    gelir = Decimal("0.00")

    if partner.financial_profile:
        if partner.financial_profile.gelir:
            gelir = partner.financial_profile.gelir