from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from datetime import datetime, timezone

from common.models import *

class CountryListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    formalName = serializers.CharField(source = "formal_name")
    iso2 = serializers.CharField()
    iso3 = serializers.CharField()
    dialCode = serializers.CharField(source = "dial_code")
    emoji = serializers.CharField()
    flag = serializers.CharField()

class CityListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    country = serializers.SerializerMethodField()
    name = serializers.CharField()
    
    def get_country(self, obj):
        return obj.country.name if obj.country else ''
    
class CurrencyListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()
    symbol = serializers.CharField()
    exchange_rate = serializers.DecimalField(max_digits=10,decimal_places=4)

class ImportProcessListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user = serializers.SerializerMethodField()
    model_name = serializers.CharField()
    task_id = serializers.CharField()
    status = serializers.CharField()
    progress = serializers.IntegerField()
    
    def get_user(self, obj):
        return obj.user.email if obj.user else ''

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