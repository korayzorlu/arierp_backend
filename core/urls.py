"""
URL configuration for marswide_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/clearcache/', include('clearcache.urls')),

    path('api/accounting/', include("accounting.urls")),
    path('api/common/', include("common.urls")),
    path('api/companies/', include("companies.urls")),
    path('api/converters/', include("converters.urls")),
    path('api/data/', include("data.urls")),
    path('api/mikro/', include("mikro.urls")),
    path('api/notifications/', include("notifications.urls")),
    path('api/partners/', include("partners.urls")),
    path('api/products/', include("products.urls")),
    path('api/subscriptions/', include("subscriptions.urls")),
    path('api/users/', include("users.urls")),
    
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    #path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)