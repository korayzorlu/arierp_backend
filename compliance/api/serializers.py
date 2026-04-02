from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from compliance.models import *
from .filters import BlackListPersonFilter
    
class BlackListPersonListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    name = serializers.CharField()
    tc_vkn_passport_no = serializers.CharField()
    other_names = serializers.CharField()
    nationality = serializers.CharField()
    birthday = serializers.CharField()
    organization = serializers.CharField()
    date_number = serializers.CharField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
class ScanPartnerListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    crm_code = serializers.CharField()
    name = serializers.CharField()
    tc_vkn_no = serializers.SerializerMethodField()
    is_scan = serializers.BooleanField()
    last_scan_date = serializers.DateTimeField()
    next_scan_date = serializers.DateTimeField()
    is_reliable_person = serializers.BooleanField()

    def get_tc_vkn_no(self, obj):
        return obj.vat_no if obj.customer_type == "institutional" else obj.tc_vkn_no
    
class PepPartnerListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    crm_code = serializers.CharField()
    name = serializers.CharField()
    tc_vkn_no = serializers.SerializerMethodField()
    email = serializers.CharField()
    birthday = serializers.DateField()
    sgk_job_code = serializers.CharField()
    is_pep = serializers.BooleanField()
    pep_degree = serializers.SerializerMethodField()
    pep_description = serializers.CharField()
    salaried_title = serializers.CharField()

    def get_tc_vkn_no(self, obj):
        return obj.vat_no if obj.customer_type == "institutional" else obj.tc_vkn_no
    
    def get_pep_degree(self, obj):
        return obj.get_pep_degree_display() if obj.pep_degree else ''
    
class ThirdPersonListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    companyId = serializers.SerializerMethodField()
    name = serializers.CharField()
    tc_vkn_no = serializers.CharField()
    status = serializers.CharField()
    created_date = serializers.DateTimeField()
    updated_date = serializers.DateTimeField()
    results = serializers.JSONField()
    third_person_documents = serializers.SerializerMethodField()
    finmaks_transactions = serializers.SerializerMethodField()
    is_email_sent = serializers.BooleanField()
    is_customer_sent = serializers.BooleanField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_third_person_documents(self, obj):
        documents = obj.third_person_third_person_documents.all()
        documents_urls = []
        if documents:
            for document in documents:
                documents_urls.append({
                        "label" : document.label,
                        "url" : document.file.url
                    })
            return documents_urls
        else:
            return []
        
    def get_finmaks_transactions(self, obj):
        finmaks_transactions = []
        bank_activities = obj.bank_activities.all().order_by('-finmaks_transaction__transaction_date')
        if bank_activities:
            for bank_activity in bank_activities:
                finmaks_transaction = {
                    "id": bank_activity.finmaks_transaction.uuid,
                    "transaction_date": bank_activity.finmaks_transaction.transaction_date.strftime("%d.%m.%Y %H:%M") if bank_activity.finmaks_transaction.transaction_date else "",
                    "transaction_id": bank_activity.finmaks_transaction.transaction_id,
                    "explanation_field": bank_activity.finmaks_transaction.explanation_field,
                    "amount": bank_activity.finmaks_transaction.amount,
                    "currency": bank_activity.finmaks_transaction.bank_account.currency.code,
                    "bank_name": bank_activity.finmaks_transaction.bank_account.bank_name,
                    "bank_account_no": bank_activity.finmaks_transaction.bank_account.account_no,
                }
                finmaks_transactions.append(finmaks_transaction)
        return finmaks_transactions
    
class ThirdPersonDocumentListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    companyId = serializers.SerializerMethodField()
    label = serializers.CharField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    
# from rest_framework import serializers
# from rest_framework.utils import html, model_meta, representation
# from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

# from decimal import Decimal
# from datetime import date,timedelta,datetime
# from django.utils import timezone

# from risk.models import *
# from leasing.utils.common_utils import vendor_filter_for_serializers,max_overdue_days,total_overdue_amount,total_temerrut_amount,paid_rate,project_filter_for_serializers,processed_amount
# from contracts.models import WarningNotice

# class RiskPartnerLiwstSerializer(serializers.Serializer):
#     id = serializers.CharField(source = "uuid")
#     crm_code = serializers.CharField()
#     name = serializers.CharField()
#     tc_vkn_no = serializers.SerializerMethodField()
#     leases = serializers.SerializerMethodField()
#     special = serializers.SerializerMethodField()
#     barter = serializers.SerializerMethodField()
#     virman = serializers.SerializerMethodField()
#     status = serializers.SerializerMethodField()
#     is_commercial = serializers.BooleanField()
#     partner_note_count = serializers.SerializerMethodField()

#     def get_tc_vkn_no(self, obj):
#         return obj.vat_no if obj.customer_type == "institutional" else obj.tc_vkn_no
    
#     def get_special(self, obj):
#         return True if "special" in obj.types else False
    
#     def get_barter(self, obj):
#         return True if "barter" in obj.types else False
    
#     def get_virman(self, obj):
#         return True if "virman" in obj.types else False
    
#     def get_status(self, obj):
#         warningNotices = WarningNotice.objects.select_related("contract__partner").filter(contract__partner = obj)
#         if warningNotices:
#             return "İhtar Çekildi"
#         else:
#             return ""
        
#     def get_partner_note_count(self, obj):
#         return obj.partner_partner_notes.count() if obj.partner_partner_notes.exists() else 0
    
#     def get_leases(self, obj):
#         request = self.context.get('request')
#         filter_params = request.GET if request else {}
        
#         leases = Lease.objects.select_related("contract","contract__partner","contract__vendor").prefetch_related("contract__contract_warning_notices").filter(
#             Q(contract__partner = obj) &
#             vendor_filter_for_serializers(filter_params) &
#             Q(overdue_amount__gt=100) &
#             Q(overdue_days__gt=0) &
#             Q(overdue_days__lte=25) &
#             Q(contract__contract_warning_notices__isnull=True) &
#             #Q(contract__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
#             (
#                 Q(lease_status='aktiflestirildi') |
#                 Q(lease_status='planlandi') |
#                 Q(lease_status='durduruldu')
#             ) &
#             Q(is_last_project=True) &
#             Q(is_kdv_diff=False) &
#             Q(is_credit=False) &
#             Q(is_under_review=False)
#         ).order_by("-overdue_days")

#         # if str(filter_params.get('project')) == "diger":
#         #     leases = leases.exclude(contract__vendor__crm_code__in=["11802","20559","1202","28974","6548"])
#         # elif str(filter_params.get('project')) == "kizilbuk":
#         #     leases = leases.filter(contract__vendor__crm_code__in=["11802","20559"])
#         # else:
#         #     leases = leases.filter(contract__vendor__crm_code=str(filter_params.get('project')))

#         lease_dict = {"leases": [],"total_overdue_amount": total_overdue_amount(leases), "max_overdue_days": max_overdue_days(leases) }
#         if leases:
#             for lease in leases:

#                 if lease.contract.contract_warning_notices.filter(Q(state__in=['Yeni', 'Geçerli'])).exists():
#                     status = "İhtar Çekildi"
#                 elif lease.is_kdv_diff:
#                     status = "KDV Farkı"
#                 elif lease.overdue_amount > 1000 and lease.overdue_days > 30:
#                     status = "İhtar Çek"
#                 else:
#                     status = "SMS"

#                 lease_dict["leases"].append({
#                     "id" : lease.uuid,
#                     "code" : lease.code,
#                     "contract" : lease.contract.code if lease.contract else "",
#                     "contract_id" : lease.contract.contract_id if lease.contract else "",
#                     "contract_uuid" : lease.contract.uuid if lease.contract else "",
#                     "partner" : lease.contract.partner.name if lease.contract.partner else "",
#                     "partner_tc" : lease.contract.partner.tc_vkn_no if lease.contract else "",
#                     "partner_crm_code" : lease.contract.partner.crm_code if lease.contract else "",
#                     "project" : lease.contract.project if lease.contract else "",
#                     "block" : lease.block or "",
#                     "unit" : lease.unit or "",
#                     "overdue_amount" : lease.overdue_amount,
#                     "overdue_days" : lease.overdue_days,
#                     "currency" : lease.currency.code if lease.currency else "",
#                     "lease_status" : lease.get_lease_status_display(),
#                     "is_kdv_diff" : lease.is_kdv_diff,
#                     "paid_rate" : lease.paid_rate,
#                     "status" : status,
#                     "overdues" : [
#                         {   
#                             'id': lease.code,
#                             'lease': lease.code,
#                             'overdue_0_30': lease.overdue_0_30,
#                             'overdue_31_60': lease.overdue_31_60,
#                             'overdue_61_90': lease.overdue_61_90,
#                             'overdue_91_120': lease.overdue_91_120,
#                             'overdue_121_150': lease.overdue_121_150,
#                             'overdue_151_180': lease.overdue_151_180,
#                             'overdue_181_gte': lease.overdue_181_gte,
#                         }
#                     ]
#                 })
#         #return sorted(lease_dict, key=lambda x: x["leases"]["overdue_days"], reverse=True)
#         return lease_dict
