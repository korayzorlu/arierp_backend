from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string

from .models import *
from users.models import User
from common.models import Currency

import os
import json

# Create your views here.

class AddCompanyView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        image = request.FILES.get('image')
        name = data.get('name')
        formal_name = data.get('formalName')

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        if not name or not formal_name:
            return JsonResponse({'message': 'Register failed! Fill required fields.','status':'error'}, status=400)

        company = Company.objects.create(
            user = request.user,
            name = name,
            formal_name = formal_name
        )

        if image:
            old_image_path = company.image.path if company.image else ""
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
            
            filePath = f"images/companies/{company.id}/{image.name}"
            savedPath = default_storage.save(filePath, ContentFile(image.read()))
            company.image = savedPath

        company.save()

        user_companies = request.user.user_companies.all()
        if user_companies:
            user_companies.update(is_active = False)

        user_company = UserCompany.objects.create(
            user = request.user,
            company = company,
            is_active = True,
            is_admin = True
        )

        user_company.save()

        return JsonResponse({'message': 'Created successfully!','status':'success'}, status=200)
    
class UpdateCompanyView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        image = request.FILES.get('image')
        removeImage = data.get('removeImage')
        name = data.get('name')
        formal_name = data.get('formalName')
        id = data.get('id')
        
        if not name or not formal_name:
            return JsonResponse({'message': 'Register failed! Fill required fields.','status':'error'}, status=400)
        
        company = Company.objects.filter(uuid = str(id), company_users__is_admin = True, company_users__user = self.request.user).first()

        if not company:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)

        if image:
            old_image_path = company.image.path if company.image else ""
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
            
            filePath = f"images/companies/{company.id}/{image.name}"
            savedPath = default_storage.save(filePath, ContentFile(image.read()))
            company.image = savedPath

        if removeImage:
            old_image_path = company.image.path if company.image else ""
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

            company.image = None

        company.name = name
        company.formal_name = formal_name

        company.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class DeleteCompanyView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        id = data.get('id')
        
        user_companies = UserCompany.objects.filter(user = request.user).order_by("company__name")
        user_company = user_companies.filter(uuid = str(id)).first()

        company = Company.objects.filter(id = user_company.company.id, user = request.user).first()

        if not company:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)
        
        user_companies.update(is_active = False)

        company.delete()

        new_active_user_company = user_companies.first()
        if new_active_user_company:
            new_active_user_company.is_active = True
            new_active_user_company.save()

        

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)

class UpdateUserCompanyView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        id = data.get('id')
        user_email = data.get('userEmail')
        status = data.get('status')
        
        user_companies = UserCompany.objects.filter(user__email = user_email).order_by("company__name")
        user_company = user_companies.filter(uuid = str(id)).first()

        if not user_company:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)

        company = Company.objects.filter(id = user_company.company.id).first()
        self_user_company = UserCompany.objects.filter(company = company, user = self.request.user).first()

        if not self_user_company.is_admin:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)
        
        if user_company == self_user_company or company.user == user_company.user:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)
        
        print(status)

        if status == "manager":
            user_company.is_admin = True
            user_company.save()
        elif status == "staff":
            user_company.is_admin = False
            user_company.save()

        return JsonResponse({'message': 'Changed successfully!','status':'success'}, status=200)

class DeleteUserCompanyView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        id = data.get('id')
        user_email = data.get('userEmail')
        
        user_companies = UserCompany.objects.filter(user__email = user_email).order_by("company__name")
        user_company = user_companies.filter(uuid = str(id)).first()

        if not user_company:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)

        company = Company.objects.filter(id = user_company.company.id).first()
        self_user_company = UserCompany.objects.filter(company = company, user = self.request.user).first()

        if not self_user_company.is_admin:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)
        
        if user_company == self_user_company or company.user == user_company.user:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)
        
        user_companies.update(is_active = False)

        user_company.delete()

        new_active_user_company = user_companies.first()
        if new_active_user_company:
            new_active_user_company.is_active = True
            new_active_user_company.save()

        return JsonResponse({'message': 'Removed successfully!','status':'success'}, status=200)

class AddInvitationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        recipient_email = data.get('email')
        company_id = data.get('companyId')
        
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        recipient = User.objects.filter(email = recipient_email).first()

        if not recipient:
            return JsonResponse({'message': 'Failed! User not found','status':'error'}, status=400)

        company = Company.objects.filter(id = int(company_id)).first()

        user_company = UserCompany.objects.filter(user = recipient, company = company).first()

        if user_company:
            return JsonResponse({'message': 'This user is already in company.','status':'error'}, status=400)

        old_invitations = Invitation.objects.filter(recipient = recipient, company = company)
        for old_invitation in old_invitations:
            old_invitation.delete()

        invitation = Invitation.objects.create(
            sender = request.user,
            recipient = recipient,
            company = company,
            token = get_random_string(32)
        )

        invitation.save()

        return JsonResponse({'message': 'Sent successfully!','status':'success'}, status=200)
    
class ConfirmInvitationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        id = data.get('id')
        status = data.get('status')
        
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        invitation = Invitation.objects.filter(id = id, recipient = request.user).first()

        if not invitation:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)

        company = Company.objects.filter(id = invitation.company.id).first()

        if not company:
            return JsonResponse({'message': 'Sorry, something went wrong!','status':'error'}, status=400)

        if status == "accepted":
            invitation.status = "accepted"
            invitation.save()

            user_companies = request.user.user_companies.all()
            if user_companies:
                user_companies.update(is_active = False)

            user_company = UserCompany.objects.create(
                user = request.user,
                company = company,
                is_active = True,
            )
            user_company.save()

            return JsonResponse({'message':'Accepted invitation!','status':'success'}, status=200)
        elif status == "declined":
            invitation.status = "declined"
            invitation.save()

            return JsonResponse({'message':'Declined invitation!','status':'success'}, status=200)
        
class DisplayCurrencySettingsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        active_company = UserCompany.objects.filter(uuid = data.get('activeCompanyUUID')).first()

        company = Company.objects.filter(uuid = active_company.company.uuid, company_users__user = self.request.user).first()

        if not company:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)

        if not data.get('displayCurrency'):
            return JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
        
        active_company.display_currency = Currency.objects.filter(code = data.get('displayCurrency')).first()
        active_company.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)