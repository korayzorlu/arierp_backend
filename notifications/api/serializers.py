from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from datetime import datetime, timezone

from notifications.models import *
from users.models import User

class NotificationListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    message = serializers.CharField()
    navigation = serializers.CharField()
    user = serializers.SerializerMethodField()
    is_read = serializers.BooleanField()
    image = serializers.ImageField()
    created_date = serializers.SerializerMethodField()
    
    def get_user(self, obj):
        return obj.user.email if obj.user else ''
    
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
    