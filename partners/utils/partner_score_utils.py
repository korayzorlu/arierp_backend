from partners.models import IncomeTypes,FundSource,RiskStatus,ComplianceStatus,AmountTRY,Frequency

from decimal import Decimal

GELIR_SKORLARI = {
    IncomeTypes.MAAS     : (Decimal("0.00"),   Decimal("1.00")),
    IncomeTypes.TICARI   : (Decimal("50.00"),  Decimal("1.00")),
    IncomeTypes.KIRA     : (Decimal("0.00"),   Decimal("1.00")),
    IncomeTypes.YATIRIM  : (Decimal("50.00"),  Decimal("1.00")),
    IncomeTypes.KRIPTO   : (Decimal("100.00"), Decimal("1.00")),
    IncomeTypes.BELIRSIZ : (Decimal("100.00"), Decimal("1.00")),
    IncomeTypes.YOK      : (Decimal("100.00"), Decimal("1.00")),
    IncomeTypes.DIGER    : (Decimal("100.00"), Decimal("1.50")),
}

FON_SKORLARI = {
    FundSource.SATIS        : (Decimal("0.00"),   Decimal("1.00")),
    FundSource.TICARI       : (Decimal("0.00"),   Decimal("1.00")),
    FundSource.MAAS         : (Decimal("0.00"),   Decimal("1.00")),
    FundSource.MAAS_BIRIKIMI: (Decimal("0.00"),   Decimal("1.00")),
    FundSource.KIRA         : (Decimal("0.00"),   Decimal("1.00")),
    FundSource.MIRAS        : (Decimal("50.00"),  Decimal("1.00")),
    FundSource.SIRKET       : (Decimal("50.00"),  Decimal("1.00")),
    FundSource.YURTDISI     : (Decimal("100.00"), Decimal("1.50")),
    FundSource.BELIRSIZ     : (Decimal("100.00"), Decimal("2.00")),
    FundSource.KRIPTO       : (Decimal("100.00"), Decimal("1.00")),
    FundSource.YOK          : (Decimal("100.00"), Decimal("1.00")),
    FundSource.DIGER        : (Decimal("100.00"), Decimal("2.00")),
}

ISLEM_TUTARI_SKORLARI = {
    AmountTRY.RANGE_0         : (Decimal("0.00"),   Decimal("1.00")),
    AmountTRY.RANGE_0_100K    : (Decimal("0.00"),   Decimal("1.00")),
    AmountTRY.RANGE_100K_500K : (Decimal("0.00"),   Decimal("1.00")),
    AmountTRY.RANGE_500K_2M   : (Decimal("0.00"),   Decimal("1.00")),
    AmountTRY.RANGE_2M_10M    : (Decimal("50.00"),  Decimal("1.00")),
    AmountTRY.RANGE_10M_ABOVE : (Decimal("100.00"), Decimal("1.00")),
}

ISLEM_SIKLIGI_SKORLARI = {
    Frequency._0_2     : (Decimal("0.00"),   Decimal("1.00")),
    Frequency._3_4     : (Decimal("50.00"),  Decimal("1.00")),
    Frequency._5_ABOVE : (Decimal("100.00"), Decimal("1.00")),
}

ISLEM_RISKI_SKORLARI = {
    RiskStatus.RISKLI_DEGIL : (Decimal("0.00"),   Decimal("1.00")),
    RiskStatus.RISKLI       : (Decimal("100.00"), Decimal("2.00")),
}

IS_UYUMU_SKORLARI = {
    ComplianceStatus.UYUMLU       : (Decimal("0.00"),   Decimal("1.00")),
    ComplianceStatus.UYUMLU_DEGIL : (Decimal("100.00"), Decimal("1.50")),
}

class CalcPartnerScore():
    def __init__(self, financial_profile=None, partner_score=None):
        self.financial_profile = financial_profile
        self.partner_score = partner_score
        self.mr_score = Decimal("0.00")
        self.mr_weight = Decimal("0.00")

    def _sum(self, selected, table):
        for key, (score, weight) in table.items():
            if key in selected:
                self.mr_score += score * weight
                self.mr_weight += weight

    def _add(self, value, table):
        if value in table:
            score, weight = table[value]
            self.mr_score += score * weight
            self.mr_weight += weight

    def calc_gelir(self):
        self._sum(self.financial_profile.income_types, GELIR_SKORLARI)

    def calc_fon(self):
        self._sum(self.financial_profile.fund_sources, FON_SKORLARI)

    def calc_islem_davranisi(self):
        self._add(self.financial_profile.transaction_amount, ISLEM_TUTARI_SKORLARI)
        self._add(self.financial_profile.transaction_frequency, ISLEM_SIKLIGI_SKORLARI)
        self._add(self.financial_profile.transaction_risk, ISLEM_RISKI_SKORLARI)
        self._add(self.financial_profile.job_compliance, IS_UYUMU_SKORLARI)

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