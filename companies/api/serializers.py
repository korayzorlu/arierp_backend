from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from datetime import datetime, timezone

from companies.models import *
from users.models import User

class CompanyListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    image = serializers.ImageField()
    name = serializers.CharField()
    formalName = serializers.CharField(source = "formal_name")
    user = serializers.SerializerMethodField()
    
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
    
class UserCompanyListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    user = serializers.SerializerMethodField()
    userId = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    companyId = serializers.SerializerMethodField()
    is_active = serializers.BooleanField()
    is_admin = serializers.BooleanField()
    userImage = serializers.SerializerMethodField()
    display_currency = serializers.SerializerMethodField()
    
    def get_user(self, obj):
        return obj.user.email if obj.user else ''
    
    def get_userId(self, obj):
        return obj.user.id if obj.user else ''
    
    def get_owner(self, obj):
        return obj.company.user.email if obj.company.user else ''
    
    def get_company(self, obj):
        return {"name":obj.company.name,"formalName":obj.company.formal_name} if obj.company else ''
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_userImage(self, obj):
        if obj.company.user.profile and obj.company.user.profile.image and obj.company.user.profile.image.name:
            request = self.context.get('request')
            image_url = obj.company.user.profile.image.url
            if request is not None:
                return request.build_absolute_uri(image_url)
            return image_url
        return ''
    
    def get_display_currency(self, obj):
        return obj.display_currency.code if obj.display_currency else ''
    
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

class UsersInCompanyListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    is_admin = serializers.BooleanField()
    email = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    def get_email(self, obj):
        return obj.user.email if obj.user else ''
    
    def get_image(self, obj):
        if obj.user.profile and obj.user.profile.image and obj.user.profile.image.name:
            request = self.context.get('request')
            image_url = obj.user.profile.image.url
            if request is not None:
                return request.build_absolute_uri(image_url)
            return image_url
        return ''
    
class InvitationListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    sender = serializers.SerializerMethodField()
    senderImage = serializers.SerializerMethodField()
    recipient = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    created_date = serializers.SerializerMethodField()
    
    def get_sender(self, obj):
        return obj.sender.email if obj.sender else ''
    
    def get_senderImage(self, obj):
        if obj.sender.profile and obj.sender.profile.image and obj.sender.profile.image.name:
            request = self.context.get('request')
            image_url = obj.sender.profile.image.url
            if request is not None:
                return request.build_absolute_uri(image_url)
            return image_url
        return ''
    
    def get_recipient(self, obj):
        return obj.recipient.email if obj.recipient else ''
    
    def get_company(self, obj):
        return obj.company.name if obj.company else ''
    
    def get_created_date(self, obj):
        now = datetime.now(timezone.utc)
        created_date = obj.created_date

        if not created_date:
            return ""

        delta = now - created_date
        total_hours = delta.total_seconds() / 3600

        if total_hours < 1:  # 1 saatten azsa dakika olarak göster
            minutes = int(delta.total_seconds() / 60)
            if minutes < 1:
                return f"{int(delta.total_seconds())} {'second' if int(delta.total_seconds()) == 1 else 'seconds'} ago"
            else:
                return f"{minutes} {'minute' if int(minutes) <= 1 else 'minutes'} ago"
        elif total_hours < 24:  # 24 saatten azsa saat olarak göster
            return f"{int(total_hours)} {'hour' if int(total_hours) == 1 else 'hours'} ago"
        elif delta.days == 1:  # Dün oluşturuldu
            return "yesterday"
        elif delta.days < 7:  # Son 7 gün içinde oluşturuldu
            return f"{delta.days}d ago"
        elif delta.days < 30:  # Haftalar içinde
            weeks = delta.days // 7
            return f"{weeks}w ago"
        elif delta.days < 365:  # Aylar içinde
            months = delta.days // 30
            return f"{months}mo ago"
        else:  # Yıllar içinde
            years = delta.days // 365
            return f"{years}y ago"

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