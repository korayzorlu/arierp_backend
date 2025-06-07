from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from products.models import *

class CategoryListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    name = serializers.CharField()

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

class ProductListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    name = serializers.CharField()
    category = serializers.SerializerMethodField()
    
    def get_category(self, obj):
        return obj.category.name if obj.category else ''

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