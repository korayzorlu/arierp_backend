from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse

from utils.mixins import CompanyOwnershipRequiredMixin

import json
from decimal import Decimal

from .models import *

# Create your views here.

class AddCategoryView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        company = Company.objects.filter(id = data.get('companyId')).first()
        active_company = request.user.user_companies.filter(is_active = True, company = company).first()

        if not company or not active_company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)

        invoice = Category.objects.create(
            company = company,
            name = data.get('name'),
        )
        invoice.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)
    
class UpdateCategoryView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Category
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        obj = Category.objects.filter(uuid = data.get('uuid')).first()
        obj.name = data.get('name')
        obj.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class DeleteCategoryView(LoginRequiredMixin,CompanyOwnershipRequiredMixin,View):
    model = Category
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        if isinstance(data.get("uuid"),str):
            obj = Category.objects.filter(uuid = data.get('uuid')).first()
            obj.delete()
        elif isinstance(data.get("uuids"),list):
            for uuid in data.get("uuids"):
                obj = Category.objects.filter(uuid = uuid).first()
                obj.delete()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)