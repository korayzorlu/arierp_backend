from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from common.models import UserActivity
from users.utils import get_client_ip


class ActivityLogService:
    @staticmethod
    def log(user, action, obj=None, extra=None, request=None):
        data = {
            "user": user,
            "action": action,
            "extra_data": extra or {},
        }
        if obj:
            data["content_type"] = ContentType.objects.get_for_model(obj)
            data["object_id"] = obj.pk
            data["object_uuid"] = obj.uuid if hasattr(obj, "uuid") else None
            data["object_repr"] = str(obj)
        if request:
            data["ip_address"] = get_client_ip(request)

        # Async yaz — DB'yi bloklama
        # transaction.on_commit(
        #     lambda: UserActivity.objects.create(**data)
        # )