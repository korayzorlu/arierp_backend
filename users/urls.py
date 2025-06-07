from django.urls import path, include
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)

from .views import *

app_name = "users"

urlpatterns = [
    path('csrf_token_get/', CSRFTokenGetView.as_view(), name="csrf_token_get"),
    path('session/', UserSessionView.as_view(), name="session"),
    path('login/', UserLoginView.as_view(), name="login"),
    path('logout/', UserLogoutView.as_view(), name="logout"),
    path('register/', UserRegisterView.as_view(), name="register"),

    path('email_settings/', UserEmailSettingsView.as_view(), name="email_settings"),
    path('email_verification/', UserEmailVerificationView.as_view(), name="email_settings"),
    path('phone_number_settings/', UserPhoneNumberSettingsView.as_view(), name="phone_number_settings"),
    path('phone_number_verification/', UserPhoneNumberVerificationView.as_view(), name="phone_number_verification"),
    path('password_settings/', UserPasswordSettingsView.as_view(), name="password_settings"),
    path('password_reset/', UserPasswordResetView.as_view(), name="password_reset"),
    path('profile_settings/', UserProfileSettingsView.as_view(), name="profile_settings"),

    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    #path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('user_information/', UserInformationView.as_view(), name="user_information"),
    
    path('api/', include("users.api.urls")),
]