from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.contrib.gis.geoip2 import GeoIP2

from users.models import *
from users.utils import get_client_ip,get_client_country
from subscriptions.models import Subscription
from common.models import Currency

class UserListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.CharField()
    is_email_verified = serializers.BooleanField()
    phone_country = serializers.SerializerMethodField()
    phone_number = serializers.CharField()
    name = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    image2 = serializers.SerializerMethodField()
    subscription = serializers.SerializerMethodField()
    theme = serializers.SerializerMethodField()
    userSourceCompanies = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    
    def get_name(self, obj):
        return obj.first_name + " " + obj.last_name if obj else ''
    
    def get_profile(self, obj):
        return obj.profile.pk if obj.profile else ''
    
    def get_subscription(self, obj):
        return obj.subscription.get_type_display() if obj.subscription else ''
    
    def get_phone_country(self, obj):
        return obj.phone_country.iso2 if obj.phone_country else ''
    
    def get_image(self, obj):
        if obj.profile and obj.profile.image and obj.profile.image.name:
            request = self.context.get('request')
            image_url = obj.profile.image.url
            if request is not None:
                return request.build_absolute_uri(image_url)
            return image_url
        return ''
    
    def get_image2(self, obj):
        if obj.profile and obj.profile.image and obj.profile.image.name:
            image_url = obj.profile.image.url
            return image_url
        return ''
    
    def get_theme(self, obj):
        return obj.profile.theme if obj.profile else ''
    
    def get_userSourceCompanies(self, obj):
        return []
    
    def get_location(self, obj):
        ip = get_client_ip(self.context.get("request"))
        country = get_client_country("68.82.141.91")
        currency = Currency.objects.filter(countries__iso2=country).first()
        curr = currency.code if currency else ""
        return {"country":country,"currency":curr}
    
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
    
class UserProfileListSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    user = serializers.SerializerMethodField()
    theme = serializers.CharField()
    
    def get_user(self, obj):
        return obj.user.id if obj.user else ''
    
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
    

