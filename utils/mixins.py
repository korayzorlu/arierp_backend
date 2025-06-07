from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from companies.models import Company

import json

class CompanyOwnershipRequiredMixin:
    model = None

    def get_object(self):
        data = json.loads(self.request.body)
        obj_uuid = data.get("uuid")

        if not self.model:
            raise ValueError("When using CompanyOwnershipRequiredMixin 'model' must be specified.")
        
        return get_object_or_404(self.model, uuid=obj_uuid)
    
    def get_queryset(self):
        data = json.loads(self.request.body)
        uuids = data.get("uuids", [])

        if not self.model:
            raise ValueError("When using CompanyOwnershipRequiredMixin, 'model' must be specified.")

        return self.model.objects.filter(uuid__in=uuids)

    def dispatch(self, request, *args, **kwargs):
        data = json.loads(self.request.body)
        if data.get("uuid"):
            obj = self.get_object()
            companies = Company.objects.filter(company_users__user = self.request.user)
            
            if not obj.company in companies:
                raise PermissionDenied("Bu objeyi düzenleme yetkiniz yok.")
        elif data.get("uuids"):
            queryset = self.get_queryset()
            companies = Company.objects.filter(company_users__user=self.request.user)

            unauthorized_objects = queryset.exclude(company__in=companies)
            if unauthorized_objects.exists():
                raise PermissionDenied("Bu objeleri düzenleme yetkiniz yok.")
        
        return super().dispatch(request, *args, **kwargs)