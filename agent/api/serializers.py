from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from agent.models import *

class AgentTaskListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    uuid = serializers.CharField()
    status = serializers.CharField()
    agent_name = serializers.CharField()
    running = serializers.SerializerMethodField()

    def get_running(self, obj):
        return True if obj.status in ['pending', 'in_progress'] else False