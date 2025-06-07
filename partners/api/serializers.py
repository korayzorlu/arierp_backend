from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from partners.models import *
from companies.models import Company,UserCompany

class PartnerListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    image = serializers.ImageField()
    name = serializers.CharField()
    formalName = serializers.CharField(source = "formal_name")
    types = serializers.ListField()
    customer = serializers.SerializerMethodField()
    supplier = serializers.SerializerMethodField()
    shareholder = serializers.SerializerMethodField()
    companyId = serializers.SerializerMethodField()
    vatOffice = serializers.CharField(source = "vat_office")
    vatNo = serializers.CharField(source = "vat_no")
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
    
    def get_customer(self, obj):
        return True if "customer" in obj.types else False
    
    def get_supplier(self, obj):
        return True if "supplier" in obj.types else False

    def get_shareholder(self, obj):
        return True if "shareholder" in obj.types else False
    
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