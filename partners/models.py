from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.utils.translation import gettext_lazy as _

from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField

import uuid
from decimal import Decimal

from companies.models import Company
from common.models import Country,City
from common.utils.mixins import CompletionRateMixin
from users.models import User

# Create your models here.

class IncomeTypes(models.TextChoices):
    MAAS = 'maas', 'Maaş'
    TICARI = 'ticari', 'Ticari Kazanç'
    KIRA = 'kira', 'Kira Geliri'
    YATIRIM = 'yatirim', 'Yatırım Geliri'
    DIGER = 'diger', 'Diğer'

class FundSource(models.TextChoices):
    SATIS = 'satis', 'Satış Geliri'
    MAAS = 'maas', 'Maaş Birikimi'
    KIRA = 'kira', 'Kira Geliri'
    MIRAS = 'miras', 'Miras'
    SIRKET = 'sirket', 'Şirket Kazancı'
    YURTDISI = 'yurtdisi', 'Yurt Dışı Transfer'
    DIGER = 'diger', 'Diğer'

class Institution(models.TextChoices):
    OZEL = 'ozel', 'Özel Sektör'
    KAMU = 'kamu', 'Kamu Kurumu'
    SERBEST = 'serbest', 'Serbest Meslek'
    EMEKLI = 'emekli', 'Emekli'
    OGRENCI = 'ogrenci', 'Öğrenci'
    EV = 'ev', 'Ev Hanımı'
    YOK = 'yok', 'Yok'

class Position(models.TextChoices):
    CALISAN = 'calisan', 'Çalışan'
    YONETICI = 'yonetici', 'Yönetici'
    ORTAK = 'ortak', 'Ortak'
    YOK = 'yok', 'Yok'

class AmountTRY(models.TextChoices):
    RANGE_0 = '0', '0 TL'
    RANGE_0_100K   = '1', '1-100.000'
    RANGE_100K_500K  = '2', '100.001-500.000'
    RANGE_500K_2M = '3', '500.001-2.000.000'
    RANGE_2M_10M = '4', '2.000.001-10.000.000'
    RANGE_10M_ABOVE = '5', '10.000.001 ve üzeri'

class Frequency(models.TextChoices):
    RANGE_0 = '0', '0'
    RANGE_1_20   = '1', '1-20'
    RANGE_21_50  = '2', '21-50'
    RANGE_51_100 = '3', '51-100'
    RANGE_101_500 = '4', '101-500'
    RANGE_500_ABOVE = '5', '500 ve üzeri'

class RiskStatus(models.TextChoices):
    RISKLI = 'riskli', 'Riskli'
    RISKLI_DEGIL   = 'riskli_degil', 'Riskli Değil'

class ComplianceStatus(models.TextChoices):
    UYUMLU = 'uyumlu', 'Uyumlu'
    UYUMLU_DEGIL   = 'uyumlu_degil', 'Uyumlu Değil'

class CustomerType(models.TextChoices):
    BIREYSEL = 'bireysel', 'Bireysel'
    TUZEL   = 'tuzel', 'Tüzel'

class CompanyType(models.TextChoices):
    AS = 'as', 'A.Ş.'
    LTD   = 'ltd', 'LTD'
    SAHIS = 'sahis', 'Şahıs Şirketi'
    KOLLEKTIF = 'kollektif', 'Kollektif Şirket'

class RemitterType(models.TextChoices):
    KENDISI = 'kendisi', 'Kendisi'
    YAKINI = 'yakini', 'Yakını (Aile Bağı)'
    UCUNCU_KISI = 'ucuncu_kisi', '3. Kişi'

class Sector(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sectors")

    code = models.CharField(_("Code"), max_length=50)
    name = models.CharField(_("Name"), max_length=250)

    main_sector_code = models.CharField(_("Main Sector Code"), max_length=50, null=True, blank=True)
    match_code = models.CharField(_("Match Code"), max_length=50, null=True, blank=True)
    kkbmb_sector_code = models.CharField(_("KKBMB Sector Code"), max_length=50, null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
    
class SgkJob(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sgk_jobs")

    sgk_job_id = models.CharField(_("SGK Job ID"), max_length=50, null=True, blank=True)
    sgk_job_code = models.CharField(_("SGK Job Code"), max_length=50, null=True, blank=True)
    description = models.CharField(_("Description"), max_length=250, null=True, blank=True)
    is_pep = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.description)

class Partner(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="partners")

    first_name = models.CharField(_("First Name"), max_length=140, blank=True, null=True)
    last_name = models.CharField(_("Last Name"), max_length=140, blank=True, null=True)

    name = models.CharField(_("Partner Name"), max_length=140, null=True, blank=True)
    formal_name = models.CharField(_("Partner Formal Name"), max_length=140, null=True, blank=True)
    image = models.ImageField(_("Image"), upload_to='media/docs/partners/ ', null=True, blank=True,
                              help_text=_("Please upload a square image, otherwise center will be cropped."))
    
    TYPES_CHOICES = (
        ('customer', ('Customer')),
        ('supplier', ('Supplier')),
        ('shareholder', ('Shareholder')),
        ('special', ('Special')),
        ('pep', ('PEP')),
        ('barter', ('Barter')),
        ('virman', ('Virman')),
    )
    types = ArrayField(models.CharField(_("Status"), max_length=25, choices=TYPES_CHOICES), default=list, blank=True, null=True)

    CUSTOMER_TYPES_CHOICES = (
        ('individual', ('Individual')),
        ('institutional', ('Institutional')),
    )
    customer_type = models.CharField(_("Customer Type"), max_length=25, default='individual', choices=CUSTOMER_TYPES_CHOICES, blank=True, null=True)

    customer_code = models.CharField(_("Customer Code"), max_length=25, blank=True, null=True)
    crm_code = models.CharField(_("CRM Code"), max_length=25, blank=True, null=True)


    vat_office = models.CharField(_("Vat Office"), max_length=50, blank=True, null=True)
    vat_no = models.CharField(_("Vat No"), max_length=50, blank=True, null=True)
    tc_no = models.CharField(_("TC No"), max_length=50, blank=True, null=True)
    tc_vkn_no = models.CharField(_("TC/VKN No"), max_length=50, blank=True, null=True)
    passport_no = models.CharField(_("Passport No"), max_length=50, blank=True, null=True)

    ticari_sicil_no = models.CharField(_("Ticari Sicil No"), max_length=50, blank=True, null=True)
    kep = models.CharField(_("Kep"), max_length=140, blank=True, null=True)
    kep_expiry_date = models.DateField(_("Kep Expiry Date"), blank=True, null=True)
    is_turkkep = models.BooleanField(default=False)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="sector_partners", blank=True, null=True)

    father_name = models.CharField(_("Father Name"), max_length=140, blank=True, null=True)
    birthday = models.DateField(_("Birthday"), blank=True, null=True)
    birth_place = models.CharField(_("Birth Place"), max_length=140, blank=True, null=True)

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name="country_partners")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, blank=True, null=True, related_name="city_partners")
    address = models.CharField(_("Address"), max_length=250, blank=True, null=True)
    address2 = models.CharField(_("Address 2"), max_length=250, blank=True, null=True)
    is_billing_same = models.BooleanField(default=False)
    billing_country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name="billing_country_partners")
    billing_city = models.ForeignKey(City, on_delete=models.SET_NULL, blank=True, null=True, related_name="billing_city_partners")
    billing_address = models.CharField(_("Billing Address"), max_length=150, blank=True, null=True)
    billing_address2 = models.CharField(_("Billing Address 2"), max_length=150, blank=True, null=True)

    phone_country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True, related_name="phone_country_partners")
    phone_number = models.CharField(_("Phone Number"), max_length=25, blank=True, null=True)
    email = models.EmailField(_("Email"), max_length=100, blank=True, null=True)
    web = models.CharField(_("Web"), max_length=250, blank=True, null=True)

    about = models.TextField(_("About"), blank = True, null = True)

    advance_amount = models.DecimalField(_("Advance Amount"), default = 0.00, max_digits=14, decimal_places=2)

    is_scan = models.BooleanField(default=False)
    last_scan_date = models.DateTimeField(_("Last Scan Date"), blank=True, null=True)
    next_scan_date = models.DateTimeField(_("Next Scan Date"), blank=True, null=True)
    is_reliable_person = models.BooleanField(default=False)
    is_commercial = models.BooleanField(default=False)

    sgk_job = models.ForeignKey(SgkJob, on_delete=models.SET_NULL, blank=True, null=True, related_name="sgk_job_partners")
    sgk_job_code = models.CharField(_("SGK Job Code"), max_length=50, blank=True, null=True)
    salaried_title = models.CharField(_("Salaried Title"), max_length=250, blank=True, null=True)
    is_pep = models.BooleanField(default=False)
    PEP_DEGREE_CHOICES = (
        ('1', ('Kendisi')),
        ('2', ('Birinci Derece Yakını')),
    )
    pep_degree = models.CharField(_("Pep Degree"), max_length=25, default='kendisi', choices=PEP_DEGREE_CHOICES, blank=True, null=True)
    pep_description = models.CharField(_("Pep Description"), max_length=500, blank=True, null=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.formal_name is None:
            self.formal_name = self.name
        is_new = self.pk is None

        super(Partner, self).save(*args, **kwargs)

        if is_new:
            PartnerFinancialProfile.objects.create(
                partner=self,
                company=self.company
            )

    def __str__(self):
        return str(self.name)

class PartnerNote(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="partner_notes")

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, blank=True, null=True, related_name="partner_partner_notes")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="user_partner_notes")
    title = models.CharField(_("Title"), max_length=140, blank=True, null=True)
    text = models.CharField(_("Text"), max_length=1000, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.user.get_full_name()} - {self.title}")

class PartnerFinancialProfile(models.Model,CompletionRateMixin):
    COMPLETION_FIELDS = [
        "income_types", "fund_sources","sgk_job", "institution", "position",
        "real_estate_assets", "vehicle_assets", "bank_deposit_assets", "investment_assets",
        "transaction_amount", "transaction_frequency", "transaction_risk", "job_compliance",
        "customer_type", "remitter_type"
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="partner_financial_profiles")

    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, primary_key=True, related_name="partner_financial_profile")
    income_types = ArrayField(models.CharField(_("Income Types"), max_length=25, choices=IncomeTypes.choices), default=list, blank=True, null=True)
    other_income = models.CharField(_("Other Income"), max_length=140, blank=True, null=True)

    fund_sources = ArrayField(models.CharField(_("Fund Sources"), max_length=25, choices=FundSource.choices), default=list, blank=True, null=True)
    other_fund_source = models.CharField(_("Other Fund Source"), max_length=140, blank=True, null=True)

    sgk_job = models.ForeignKey(SgkJob, on_delete=models.SET_NULL, blank=True, null=True, related_name="sgk_job_partner_financial_profiles")
    institution = models.CharField(_("Institution"), max_length=25, choices=Institution.choices, blank=True, null=True)
    position = models.CharField(_("Position"), max_length=25, choices=Position.choices, blank=True, null=True)

    real_estate_assets = models.CharField(_("Real Estate Assets"), max_length=25, choices=AmountTRY.choices, blank=True, null=True)
    vehicle_assets = models.CharField(_("Vehicle Assets"), max_length=25, choices=AmountTRY.choices, blank=True, null=True)
    bank_deposit_assets = models.CharField(_("Bank Deposit Assets"), max_length=25, choices=AmountTRY.choices, blank=True, null=True)
    investment_assets = models.CharField(_("Investment Assets"), max_length=25, choices=AmountTRY.choices, blank=True, null=True)
    other_assets = models.CharField(_("Other Assets"), max_length=25, choices=AmountTRY.choices, blank=True, null=True)
    # other_assets = models.DecimalField(_("Other Assets"), default = Decimal("0.00"), max_digits=14, decimal_places=2)

    transaction_amount = models.CharField(_("Transaction Amount"), max_length=25, choices=AmountTRY.choices, blank=True, null=True)
    transaction_frequency = models.CharField(_("Transaction Frequency"), max_length=25, choices=Frequency.choices, blank=True, null=True)
    transaction_risk = models.CharField(_("Transaction Risk"), max_length=25, choices=RiskStatus.choices, blank=True, null=True)
    job_compliance = models.CharField(_("Job Compliance"), max_length=25, choices=ComplianceStatus.choices, blank=True, null=True)

    customer_type = models.CharField(_("Customer Type"), max_length=25, choices=CustomerType.choices, blank=True, null=True)
    is_foreign_nationality = models.BooleanField(default=False)
    is_end_beneficiary = models.BooleanField(default=False)

    is_transparency = models.BooleanField(default=False)
    is_foreign_partner = models.BooleanField(default=False)
    is_complex_partner = models.BooleanField(default=False)

    is_pep = models.BooleanField(default=False)
    is_negative_news = models.BooleanField(default=False)

    company_type = models.CharField(_("Company Type"), max_length=25, choices=CompanyType.choices, blank=True, null=True)

    is_cash_payment = models.BooleanField(default=False)
    is_balloon_payment = models.BooleanField(default=False)
    remitter_type = models.CharField(_("Remitter Type"), max_length=25, choices=RemitterType.choices, blank=True, null=True)

    is_suspicious = models.BooleanField(default=False)
    is_blacklisted = models.BooleanField(default=False)

    is_warning_notice = models.BooleanField(default=False)
    is_delayed = models.BooleanField(default=False)
    is_kkb_score_low = models.BooleanField(default=False)
    is_administrative_follow_up = models.BooleanField(default=False)
    is_cheque_risk = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.partner.name}")


class PartnerScore(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="partner_scores")

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, blank=True, null=True, related_name="partner_partner_scores")
    score = models.DecimalField(_("Score"), default = Decimal("0.00"), max_digits=14, decimal_places=2)
    description = models.TextField(_("Description"), max_length=5000, blank = True, null = True)

    #risk yönetim programı >> ekran: Risk Yönetimi
        #3 seviye olacak, düşük/orta/yüksek
            #müşteri riski
                #birey
                    #meslek/çalıştığı kurum >> meslek listesi içeriye eklenecek ve gruplanacak
                    #yerleşim yeri >> şehir listesi gruplanacak
                        #hatay,kilis,gaziantep,ş.urfa,mardin,şırnak,hakkari,van,ağrı,ığdır,kars,ardahan >> bu şehirlerde ekstra risk puanı yükselecek, diğer tüm şehirler risksiz
                    #yaş >> 18-25 yaş arası risk yüksek, 65 yaş üstü yüksek riskli. diğerlerinde risk yok.
                    #pep grubu >> kendisi, birinci derece yakını, ikinci derece yakını riskli olacak.
                    #gerçek faydalanıcı belirli ya da belirsiz >> gerçek faydalanıcı belirli ise riski az değilse riski yüksek olacak
                    #olumsuz haber >> olumsuz haber varsa risk yüksek olacak
                    #şüpheli işlem bildirimi >> şüpheli işlem bildirimi varsa risk yüksek olacak
                    #uyruk >> riskli ülkeler listesi oluşturulacak, o ülkelerden olan müşterilerin riski yüksek olacak
                    #mali profil >> risk merkezinden çekilen mali profil arınet üzerinde hazırlanacak bir ekrana girilecek. bu veri oradan beslenecek.
                        #gelir türü (tik/select)
                            #maaş
                            #ticari kazanç
                            #kira geliri
                            #yatırım geliri
                            #diğer(doldurulabilri olacak)
                        #iş ve meslek 
                            #meslek/sektör (seçmeli/select box)
                            #çalıştığı kurum (seçmeli/select box)
                            #pozisyon(çalışan,yönetici,ortak) (seçmeli/select box)
                        #varlıklar 
                            #taşınmaz (seçmeli/gruplama)
                            #araçlar (seçmeli/gruplama)
                            #banka mevduatı (seçmeli/gruplama)
                            #yatırımlar(altın,hisse senedi vb.) (seçmeli/gruplama)
                            #diğer (açık uçlu doldurulabilir)
                        #fon kaynağı 
                            #satış geliri (tik/select)
                            #maaş birikimi (tik/select)
                            #kira geliri (tik/select)
                            #miras (tik/select)
                            #şirket kazancı (tik/select)
                            #yurt dışı transfer (tik/select)
                            #diğer (açık uçlu doldurulabilir)
                        #işlem davranışı
                            #ortalama işlem tutarı (seçmeli/gruplama)
                            #işlem sıklığı (seçmeli/gruplama)
                            #gelire göre normal/anormal (seçmeli/gruplama) >> profil işlem uyumundaki seçenekler gelecek
                            #gelir meslek uyumlu mu? (seçmeli/gruplama)
                        #müşteri tipi
                            #bireysel (tik/select)
                            #tüzel (tik/select)
                            #yabancı uyruk (tik/select)
                            #nihai faydalanıcı mı? (tik/select)
                        #şirket yapısı
                            #şeffaf (tik/select)
                            #yabancı ortaklı (tik/select)
                            #çok ortaklı karmaşık (tik/select)
                        #şirket türü
                            #a.ş. (tik/select)
                            #ltd. şirket (tik/select)
                            #şahıs şirketi (tik/select)
                            #kollektif şirket (tik/select)
                        #pep ve itibar kontrolü
                            #pep grubu mu? (tik/select)
                            #olumsuz haber var mı? (tik/select)
                        #ödeme davranışı
                            #nakit ödeme (tik/select)
                            #3.kişi kullanımı (tik/select) >> kendi, 3. kişi ve yakını(aile bağı) olarak seçenek koyulacak
                            #parçalı ödeme(balon ödeme) (tik/select)
                        #kritik alan kontrolü
                            #şüpheli işlem bildirimi var mı? (tik/select)
                            #yasaklı listesinde yer alıyor mu? (tik/select)
                        #profil işlem uyumu
                            #gelir > işlem tutarı & gelir = işlem tutarı >> risksiz (tik/select)
                            #gelir < işlem tutarı >> riskli (tik/select)
                        #ödeme performansı
                            #birey
                                #ihtar var mı?(arı ihtarı) (tik/select)
                                #gecikme var mı? (tik/select)
                                #kkb puanı (seçmeli/gruplama)
                                #idari,kanuni takip ve varlık yönetim şirketine devir var mı? (tik/select)
                            #tüzel
                                #ihtar var mı? (tik/select)
                                #gecikme var mı? (tik/select)
                                #kkb puanı (seçmeli/gruplama)
                                #idari,kanuni takip ve konkordata var mı? (tik/select)
                                #çek senet riski var mı? (tik/select)

                    #yaptırım listeleri >> yaptırım listelerinde yer alıyorsa riskli, değilse risk yok
                #tüzel
                    #kuruluş yılı >> kuruluş yılı 2 yıldan az ise risk yüksek, 10 yıldan fazla ise risk düşük, diğerlerinde risk yok
                    #kuruluş yeri >> kuruluş yeri şehir olarak gruplanacak, hatay,kilis,gaziantep,ş.urfa,mardin,şırnak,hakkari,van,ağrı,ığdır,kars,ardahan >> bu şehirlerde ekstra risk puanı yükselecek, diğer tüm şehirler risksiz
                    #gerçek faydalanıcı belirli ya da belirsiz >> gerçek faydalanıcı belirli ise riski az değilse riski yüksek olacak
                    #olumsuz haber >> olumsuz haber varsa risk yüksek olacak
                    #şüpheli işlem bildirimi >> şüpheli işlem bildirimi varsa risk yüksek olacak
                    #yaptırım listeleri >> yaptırım listelerinde yer alıyorsa riskli, değilse risk yok
                    #faaliyet işlem uyumu >> tam uyumlu,kısmi uyumlu, ciddi uyumsuzluk şeklinde gruplanacak. düşük/orta/yüksek şeklinde.
                    #sektör riski >> sektötler nace üzerinden gruplandı bu veriler içeriye aktarılacak, sektör riski barındıranların riski yüksek
                    #ortaklık yapısı >> şeffaf yapı, yabancı ortak, çok ortaklı karmaşık yapı şeklinde gruplanacak. karmaşık en riskli, yabancı ortak orta, şeffaf yapı düşük riskli.
                    #şirket türü >> anonim şirket,limited şirket düşük, şahıs şirketi orta, kollektif şirket yüksek riskli olacak
            #ürün hizmet riski
                #erken kapama ya da tadil riski >> erken kapama ya da tadil riski yüksek olan ürünler belirlenecek, o ürünlerde yapılan işlemler riskli olacak
                #kiracı değişikliği >> kiracı değişikliği riski arttıracak değişiklik yok ise risk düşük(devreden taraf)
                #vekaletle işlemler >> vekaletle yapılan işlemler riskli olacak
                #lüks segment >> 20 milyon tl üstü işlemler yüksek riskli olacak
                #ticari alımlar >> ticari alımlar riskli olacak
                #yabancıya satış >> yabancıya satış riskli olacak(çok yüksek)
                #sat geri kirala >> sat geri kirala işlemi riskli olacak
            #coğrafi risk
                #ülke ve şehir riski >> 12 şehir varsa yüksek grup, riskli ülkeler de riskli grup olacak
            #ödeme ve dağıtım kanalları riski
                #sanal pos >> sanal pos kullanımı riskli olacak
                #muhabir banka >> muhabir banka kullanımı riskli olacak
                #ödeme kuruluşu >> ödeme kuruluşu kullanımı riskli olacak
                #nakit işlem >> nakit işlem riski yüksek olacak
                #anonim ödeme >> 3. kişi ödemeleri riskli olacak(en riskli alan)
                #havale/eft >> havale/eft işlemleri riskli değil(kendisi yapıyorsa)
                #çek senet >> çek ve senet işlemleri riskli olacak
            #işlem/limit/işlem hacmi riski
                #işlem hacmi
                    #düşük hacim(düşük risk)
                        #devremülk/paylı
                        #işlem adedi 3 altı(3 dahil değil)
                        #işlem miktarı 10 milyon altı(10 dahil değil)
                    #orta hacim(orta risk)
                        #konut/devremülk
                        #işlem adedi 3-5 arası(5 dahil değil)
                        #işlem limiti 10-15 milyon arası(15 dahil değil)
                    #yüksek hacim(yüksek risk)
                        #tam mülkiyet/konut
                        #işlem adedi 5 ve üzeri
                        #işlem limiti 15 milyon ve üzeri

    #izleme ve kontrol alanı

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(f"{self.partner.name} - {self.score}")




#log
auditlog.register(Partner)