from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from converters.models import *
from companies.models import Company,UserCompany

class BankaHareketiListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    gonderen_unvani = serializers.CharField()
    musteri_unvani = serializers.CharField()
    aciklama = serializers.CharField()
    ucuncu_sahis_mi = serializers.BooleanField()
    ucuncu_sahis_mi_str = serializers.CharField()

class BankaTahsilatiListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    gonderen_unvani = serializers.CharField()
    tc_vkn_no = serializers.CharField()
    aciklama = serializers.CharField()
    tutar = serializers.DecimalField(max_digits=14,decimal_places=2)

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

class BankaTahsilatiOdooListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    gonderen_unvani = serializers.CharField()
    tc_vkn_no = serializers.CharField()
    aciklama = serializers.CharField()
    tutar = serializers.DecimalField(max_digits=14,decimal_places=2)

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