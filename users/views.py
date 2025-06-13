from django.shortcuts import render,redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import BadHeaderError
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.signing import TimestampSigner,BadSignature, SignatureExpired
from django.urls import reverse
from django.contrib.gis.geoip2 import GeoIP2

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from dotenv import load_dotenv
load_dotenv()

import json
import logging
from twilio.rest import Client

from .models import *
from .utils import get_client_ip,get_client_country
from subscriptions.models import Subscription
from common.models import Country,Currency
from companies.models import Company, UserCompany

# Create your views here.

signer = TimestampSigner()

class CSRFTokenGetView(View):
    def get(self, request, *args, **kwargs):
        token = get_token(request)
        return JsonResponse({'csrfToken': token})

class UserSessionView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:

            return JsonResponse({"authenticated": True},status=200)
        return JsonResponse({"authenticated": False},status=200)

class UserLoginView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
                request.session.modified = True

            account_sid = str(os.getenv('TWILIO_ACCOUNT_SID'))
            auth_token = str(os.getenv('TWILIO_AUTH_TOKEN'))
            client = Client(account_sid, auth_token)

            service = client.verify.v2.services.create(
                friendly_name="TWilio Verify Service"
            )

            if service.sid:
                user.verify_sid = service.sid
                user.save()

            ip = get_client_ip(request)
            country = get_client_country(ip)
            currency = Currency.objects.filter(countries__iso2=country).first()
            curr = currency.code if currency else ""

            user_data = {
                'id': user.id,
                'email': user.email,
                'is_email_verified' : user.is_email_verified,
                'phone_number': user.phone_number,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name' : user.first_name + " " + user.last_name if user else '',
                'profile':user.profile.pk,
                'image': request.build_absolute_uri(user.profile.image.url) if user.profile.image else "",
                'theme': user.profile.theme,
                'userSourceCompanies': [],
                'subscription' : user.subscription.get_type_display() if user.subscription else '',
                'location' : {"country":country,"currency":curr}
            }
            return JsonResponse({'user':user_data, 'theme': user.profile.theme}, status=200)
        else:
            return JsonResponse({'message': 'Login failed! Invalid username or password.','status':'error'}, status=401)

#@method_decorator(csrf_exempt, name='dispatch')
class UserLogoutView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return JsonResponse({'success': True})
    
class UserRegisterView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        passwordConfirmation = data.get('passwordConfirmation')
        firstName = data.get('firstName')
        lastName = data.get('lastName')
        refCode = data.get('refCode')
        username = email.split('@')[0]

        if not email or not password or not passwordConfirmation or not firstName or not lastName or not refCode:
            return JsonResponse({'message': 'Register failed! Fill required fields.','status':'error'}, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'message': 'Register failed! This email address is already in use.','status':'error'}, status=400)
        
        if password != passwordConfirmation:
            return JsonResponse({'message': 'Register failed! Please make sure your passwords match.','status':'error'}, status=400)
        
        try:
            validate_password(password)
        except ValidationError as e:
            return JsonResponse({'message': ' '.join(e.messages),'status':'error'}, status=400)
        
        if refCode != "MARS2030SDXF":
            return JsonResponse({'message': 'Register failed! Invalid reference code','status':'error'}, status=400)

        user = User.objects.create_user(email=email, username=username, first_name=firstName, last_name=lastName, password=password)
        user.save()

        profile = Profile.objects.create(user = user)
        profile.save()

        company = Company.objects.filter().first()
        user_company = UserCompany.objects.create(
            user = user,
            company = company,
            is_active = True,
            is_admin = False
        )
        user_company.save()

        subscription = Subscription.objects.create(user = user)
        subscription.save()

        user = authenticate(request, email=email, password=password)
        login(request, user)

        token = signer.sign(user.email)
        verification_url = f"{os.getenv("EMAIL_PROTOCOL")}://{request.get_host()}/api/users/email_verification?token={token}"

        try:
            subject = "Verify Your Email for Marswide"
            message = f"Please verify your email by clicking the link below.\n\n{verification_url}"
            from_email = "Marswide <info@marswide.com>"
            to_email = [email]
            
            email_message = EmailMessage(
                subject,
                message,
                from_email, 
                to_email
            )

            email_message.body = message
            email_message.send()
        except:
            pass
        
        user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name' : user.first_name + " " + user.last_name if user else '',
                'profile':user.profile.pk,
                'theme': user.profile.theme,
                'userSourceCompanies': [],
                'subscription' : user.subscription.get_type_display() if user.subscription else ''
            }
        return JsonResponse({'user':user_data}, status=201)
    
class UserEmailSettingsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        email = data.get('email')

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)

        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            return JsonResponse({'message': 'This email address is already in use.','status':'error'}, status=400)
        
        token = signer.sign(request.user.email)
        verification_url = f"{os.getenv("EMAIL_PROTOCOL")}://{request.get_host()}/api/users/email_verification?token={token}"

        try:
            subject = "Verify Your Email for Marswide"
            message = f"Please verify your email by clicking the link below.\n\n{verification_url}"
            from_email = "Marswide <info@marswide.com>"
            to_email = [email]
            
            email_message = EmailMessage(
                subject,
                message,
                from_email, 
                to_email
            )

            email_message.body = message
            email_message.send()
            return JsonResponse({'message': 'Sent successfully!','status':'success'}, status=200)
        except User.DoesNotExist:
                return JsonResponse({'message': 'User not found. Please enter a valid email address.','status':'error'}, status=400)
        except BadHeaderError:
            return JsonResponse({'message': 'Invalid header.','status':'error'}, status=400)

class UserEmailVerificationView(View):
    def get(self, request, *args, **kwargs):
        token = request.GET.get("token")

        try:
            email = signer.unsign(token, max_age=86400)
            user = User.objects.get(email=email)
            user.is_email_verified = True
            user.save()
            return redirect(f"{os.getenv("BASE_URL")}/settings/auth/email")
            #return JsonResponse({'message': 'Verified successfully!','status':'success'}, status=200)
        except SignatureExpired:
                return JsonResponse({'message': 'Link expired!','status':'error'}, status=400)
        except (BadSignature, User.DoesNotExist):
            return JsonResponse({'message': 'Invalid link.','status':'error'}, status=400)

class UserPhoneNumberSettingsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        iso2 = data.get('iso2')
        phone_number = data.get('phoneNumber')

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        country = Country.objects.filter(iso2 = iso2).first()
        if not country:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)

        if User.objects.filter(phone_country=country,phone_number=phone_number).exclude(id=request.user.id).exists():
            return JsonResponse({'message': 'This phone number is already in use.','status':'error'}, status=400)
        
        if User.objects.filter(phone_country=country,phone_number=phone_number).exists():
            return JsonResponse({'message': 'Your phone number verified!','status':'error'}, status=400)
        
        account_sid = str(os.getenv('TWILIO_ACCOUNT_SID'))
        auth_token = str(os.getenv('TWILIO_AUTH_TOKEN'))
        client = Client(account_sid, auth_token)

        verification_check = client.verify.v2.services(request.user.verify_sid).verifications.create(to=f"{country.dial_code}{phone_number}", channel='sms')

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class UserPhoneNumberVerificationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        iso2 = data.get('iso2')
        phone_number = data.get('phoneNumber')
        sms_code = data.get('smsCode')

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)
        
        country = Country.objects.filter(iso2 = iso2).first()
        if not country:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)

        if User.objects.filter(phone_country=country,phone_number=phone_number).exclude(id=request.user.id).exists():
            return JsonResponse({'message': 'This phone number is already in use.','status':'error'}, status=400)
        
        account_sid = str(os.getenv('TWILIO_ACCOUNT_SID'))
        auth_token = str(os.getenv('TWILIO_AUTH_TOKEN'))
        client = Client(account_sid, auth_token)

        verification_check = client.verify.v2.services(request.user.verify_sid).verification_checks.create(to=f"{country.dial_code}{phone_number}", code=sms_code)
        
        if verification_check.status == "approved":
            user = request.user
            user.phone_country = country
            user.phone_number = phone_number
            user.save()
        else:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)

        return JsonResponse({'message': 'Verified successfully!','status':'success'}, status=200)

class UserPasswordSettingsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        newPassword = data.get('newPassword')
        newPasswordConfirmation = data.get('newPasswordConfirmation')
        
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Auth failed!.','status':'error'}, status=401)

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if newPassword != newPasswordConfirmation:
                return JsonResponse({'message': 'Please make sure your passwords match.','status':'error'}, status=400)
            
            try:
                validate_password(newPassword)
            except ValidationError as e:
                return JsonResponse({'message': ' '.join(e.messages),'status':'error'}, status=400)
            
            if password == newPassword:
                return JsonResponse({'message': 'Sorry, your new password cannot be the same as your old password.','status':'error'}, status=400)
            
            user.set_password(newPassword)
            user.save()
        else:
            return JsonResponse({'message': 'Auth failed! Invalid password.','status':'error'}, status=400)

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class UserPasswordResetView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        email = data.get('email')

        form = PasswordResetForm({'email': email})
        if form.is_valid():
            try:
                user = User.objects.get(email=email)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                context = {
                    'uid' : uid,
                    'token' : token,
                    'protocol': os.getenv("EMAIL_PROTOCOL"),
                    'domain': request.get_host()
                }

                subject = "Password Reset Request for Marswide"
                message = "Please reset your password by clicking the link below."
                html_message = render_to_string('registration/password_reset_email.html', context)
                from_email = "Marswide <info@marswide.com>"
                to_email = [email]
                
                email_message = EmailMessage(
                    subject, 
                    html_message, 
                    from_email, 
                    to_email
                )

                #email_message.body = message  # Metin içeriğini ekle

                email_message.content_subtype = "html"  # HTML içeriği olarak gönder
                email_message.send()
                return JsonResponse({'message': 'Password reset link has been sent.','status':'success'}, status=200)
            except User.DoesNotExist:
                    return JsonResponse({'message': 'User not found. Please enter a valid email address.','status':'error'}, status=400)
            except BadHeaderError:
                return JsonResponse({'message': 'Invalid header.','status':'error'}, status=400)

        return JsonResponse({'message': 'Invalid email.','status':'error'}, status=400)
    
class UserProfileSettingsView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        image = request.FILES.get('image')
        removeImage = data.get('removeImage')

        profile = request.user.profile

        if image:
            old_image_path = profile.image.path if profile.image else ""
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
            
            filePath = f"images/users/{request.user.id}/{image.name}"
            savedPath = default_storage.save(filePath, ContentFile(image.read()))
            profile.image = savedPath

        if removeImage:
            old_image_path = profile.image.path if profile.image else ""
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

            profile.image = None

        profile.save()

        return JsonResponse({'message': 'Saved successfully!','status':'success'}, status=200)
    
class UserInformationView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        email = data.get('email')

        user = User.objects.filter(email = email).first()

        if not user:
            return JsonResponse({'message' : 'Sorry, something went wrong!','status':'error'}, status=400)
        
        user_data = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name' : user.get_full_name(),
                'profile':user.profile.pk,
                'image': request.build_absolute_uri(user.profile.image.url) if user.profile.image else "",
        }

        return JsonResponse({'user':user_data}, status=200)