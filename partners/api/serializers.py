from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from partners.models import *
from companies.models import Company,UserCompany
from django.utils.timezone import localtime

class SectorListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    mainSectorCode = serializers.CharField(source = "main_sector_code")
    matchCode = serializers.CharField(source = "match_code")
    kkbmbSectorCode = serializers.CharField(source = "kkbmb_sector_code")
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
        return obj.phone_country.iso2 if obj.phone_country else ''

    def update(self, instance, validated_data):
        info = model_meta.get_field_info(instance)

        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)

        instance.save()

        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)
        
        return instance

class SgkJobListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    sgk_job_id = serializers.CharField()
    sgk_job_code = serializers.CharField()
    description = serializers.CharField()
    is_pep = serializers.BooleanField()
class PartnerListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    uuid = serializers.CharField()
    image = serializers.ImageField()
    name = serializers.CharField()
    formalName = serializers.CharField(source = "formal_name")
    types = serializers.ListField()
    customer_type = serializers.CharField()
    customerCode = serializers.CharField(source = "customer_code")
    crmCode = serializers.CharField(source = "crm_code")
    customer = serializers.SerializerMethodField()
    supplier = serializers.SerializerMethodField()
    shareholder = serializers.SerializerMethodField()
    special = serializers.SerializerMethodField()
    pep = serializers.SerializerMethodField()
    companyId = serializers.SerializerMethodField()
    vatOffice = serializers.CharField(source = "vat_office")
    vatNo = serializers.CharField(source = "vat_no")
    tcVknNo = serializers.CharField(source = "tc_vkn_no")
    country = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    address = serializers.CharField()
    address2 = serializers.CharField()
    isBillingSame = serializers.BooleanField(source = "is_billing_same")
    billingCountry = serializers.SerializerMethodField()
    billingCity = serializers.SerializerMethodField()
    billingAddress = serializers.CharField(source = "billing_address")
    billingAddress2 = serializers.CharField(source = "billing_address2")
    country_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    phoneCountry = serializers.SerializerMethodField(source = "phone_country")
    phoneNumber = serializers.CharField(source = "phone_number")
    email = serializers.EmailField()
    web = serializers.EmailField()
    about = serializers.CharField()
    is_reliable_person = serializers.BooleanField()
    is_commercial = serializers.BooleanField()
    is_turkkep = serializers.BooleanField()
    kep = serializers.CharField()
    kep_expiry_date = serializers.DateField()
    sgk_job = serializers.SerializerMethodField()
    sgk_job_code = serializers.SerializerMethodField()
    
    def get_customer(self, obj):
        return True if "customer" in obj.types else False
    
    def get_supplier(self, obj):
        return True if "supplier" in obj.types else False

    def get_shareholder(self, obj):
        return True if "shareholder" in obj.types else False
    
    def get_special(self, obj):
        return True if "special" in obj.types else False
    
    def get_pep(self, obj):
        return True if "pep" in obj.types else False
    
    def get_country(self, obj):
        return obj.country.iso2 if obj.country else ''
    
    def get_city(self, obj):
        return {"id":obj.city.id,"name":obj.city.name} if obj.city else {}
    
    def get_billingCountry(self, obj):
        return obj.billing_country.iso2 if obj.billing_country else ''
    
    def get_billingCity(self, obj):
        return {"id":obj.billing_city.id,"name":obj.billing_city.name} if obj.billing_city else {}
    
    def get_country_name(self, obj):
        return obj.country.name if obj.country else ''
    
    def get_city_name(self, obj):
        return obj.city.name if obj.city else ''
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_phoneCountry(self, obj):
        return obj.phone_country.iso2 if obj.phone_country else ''
    
    def get_sgk_job(self, obj):
        return obj.sgk_job.description if obj.sgk_job else ''

    def get_sgk_job_code(self, obj):
        return obj.sgk_job.sgk_job_code if obj.sgk_job else ''

    def update(self, instance, validated_data):
        info = model_meta.get_field_info(instance)

        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)

        instance.save()

        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)
        
        return instance
    

class PartnerNoteListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    uuid = serializers.CharField()
    user = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    title = serializers.CharField()
    text = serializers.CharField()
    date = serializers.SerializerMethodField()

    def get_user(self, obj):
        return obj.user.get_full_name() if obj.user else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ''
    
    def get_date(self, obj):
        if obj.created_date:
            return localtime(obj.created_date).strftime("%d.%m.%Y %H:%M")
        return ''
    
class PartnerFinancialProfileListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    uuid = serializers.CharField()
    partner = serializers.SerializerMethodField()
    income_types = serializers.ListField()
    other_income = serializers.CharField()
    income_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    fund_sources = serializers.ListField()
    other_fund_source = serializers.CharField()
    completion_rate = serializers.SerializerMethodField()
    sgk_job = serializers.SerializerMethodField()
    institution = serializers.CharField()
    position = serializers.CharField()
    bank_deposit_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    real_estate_assets = serializers.CharField()
    real_estate_assets_count = serializers.IntegerField()
    vehicle_assets = serializers.CharField()
    vehicle_assets_count = serializers.IntegerField()
    bank_deposit_assets = serializers.CharField()
    investment_assets = serializers.CharField()
    other_assets = serializers.CharField()
    other_assets_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    other_assets_description = serializers.CharField()
    transaction_amount = serializers.CharField()
    transaction_frequency = serializers.CharField()
    transaction_risk = serializers.CharField()
    job_compliance = serializers.CharField()
    customer_type = serializers.SerializerMethodField()
    is_foreign_nationality = serializers.BooleanField()
    is_end_beneficiary = serializers.BooleanField()
    is_transparency = serializers.BooleanField()
    is_foreign_partner = serializers.BooleanField()
    is_complex_partner = serializers.BooleanField()
    company_type = serializers.CharField()
    balance_sheet_and_capital_structure = serializers.CharField()
    is_pep = serializers.BooleanField()
    is_negative_news = serializers.BooleanField()
    is_cash_payment = serializers.BooleanField()
    is_balloon_payment = serializers.BooleanField()
    is_institutional_payment = serializers.BooleanField()
    is_correspondent_bank = serializers.BooleanField()
    is_payment_institution = serializers.BooleanField()
    is_cek_senet_payment = serializers.BooleanField()
    remitter_type = serializers.CharField()
    vpos_type = serializers.CharField()
    is_suspicious = serializers.BooleanField()
    is_blacklisted = serializers.BooleanField()
    is_offshore = serializers.BooleanField()
    is_low_tax = serializers.BooleanField()
    is_complex_structure = serializers.BooleanField()
    is_tax_haven = serializers.BooleanField()
    is_high_risk_country = serializers.BooleanField()
    is_warning_notice = serializers.BooleanField()
    is_delayed = serializers.BooleanField()
    is_kkb_score_low = serializers.BooleanField()
    is_administrative_follow_up = serializers.BooleanField()
    is_cheque_risk = serializers.BooleanField()
    partner_information_documents = serializers.SerializerMethodField()
    
    def get_partner(self, obj):
        if obj.partner.tc_vkn_no and obj.partner.tc_vkn_no != '':
            tc_vkn_no = obj.partner.tc_vkn_no
        elif obj.partner.vat_no and obj.partner.vat_no != '':
            tc_vkn_no = obj.partner.vat_no
        else:
            tc_vkn_no = ''

        return {
            "id": obj.partner.uuid if obj.partner else '',
            "name": obj.partner.name if obj.partner else '',
            "tc_vkn_no": tc_vkn_no,
            "customer_code": obj.partner.customer_code if obj.partner else '',
            "crm_code": obj.partner.crm_code if obj.partner else '',
            "customer_type": obj.partner.customer_type if obj.partner else '',
        }
    
    def get_sgk_job(self, obj):
        return obj.sgk_job.sgk_job_code if obj.sgk_job else ''
    
    def get_completion_rate(self, obj):
        return obj.get_completion_rate()
    
    def get_customer_type(self, obj):
        if obj.partner and obj.partner.customer_type == 'individual':
            return "bireysel"
        elif obj.partner and obj.partner.customer_type == 'institutional':
            return "tuzel"
        else:
            return ''
        
    def get_partner_information_documents(self, obj):
        documents = obj.partner.partner_partner_information_documents.all()
        documents_urls = []
        if documents:
            for document in documents:
                documents_urls.append({
                        "id" : document.uuid,
                        "label" : document.label,
                        "url" : document.file.url
                    })
            return documents_urls
        else:
            return []
