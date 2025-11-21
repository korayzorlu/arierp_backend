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
    
class ThirdPersonListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    companyId = serializers.SerializerMethodField()
    name = serializers.CharField()
    tc_vkn_no = serializers.CharField()
    status = serializers.CharField()
    created_date = serializers.DateTimeField()
    results = serializers.JSONField()
    third_person_documents = serializers.SerializerMethodField()
    finmaks_transaction = serializers.SerializerMethodField()
    
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
        
    def get_finmaks_transaction(self, obj):
        bank_activity = obj.bank_activities.all().first()
        if bank_activity:
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
        else:
            finmaks_transaction = None
        return finmaks_transaction
    
class ThirdPersonDocumentListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    companyId = serializers.SerializerMethodField()
    label = serializers.CharField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    
    