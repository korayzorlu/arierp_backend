from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from projects.models import *
from companies.models import Company,UserCompany
from partners.models import Partner
from contracts.models import WarningNotice
    
class ProjectListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    project_id = serializers.CharField()
    name = serializers.CharField()
    partner_crm_code = serializers.SerializerMethodField()
    partner_name = serializers.SerializerMethodField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''

    def get_partner_crm_code(self, obj):
        return obj.partner.crm_code if obj.partner else ""
    
    def get_partner_name(self, obj):
        return obj.partner.name if obj.partner else ""
    
class ParcelListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    parcel_id = serializers.CharField()
    no = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''

    def get_project(self, obj):
        return obj.project.name if obj.project else ''

class RealEstateListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    parcel = serializers.CharField()
    block = serializers.CharField()
    unit = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''

    def get_project(self, obj):
        return obj.project.name if obj.project else ''
    