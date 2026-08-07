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

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/clearcache/', include('clearcache.urls')),

    path('api/accounting/', include("accounting.urls")),
    path('api/agent/', include("agent.urls")),
    path('api/common/', include("common.urls")),
    path('api/communication/', include("communication.urls")),
    path('api/companies/', include("companies.urls")),
    path('api/compliance/', include("compliance.urls")),
    path('api/contracts/', include("contracts.urls")),
    path('api/converters/', include("converters.urls")),
    path('api/data/', include("data.urls")),
    path('api/emlak/', include("emlak.urls")),
    path('api/finance/', include("finance.urls")),
    path('api/inventory/', include("inventory.urls")),
    path('api/krs/', include("krs.urls")),
    path('api/leasing/', include("leasing.urls")),
    path('api/ledger/', include("ledger.urls")),
    path('api/mikro/', include("mikro.urls")),
    path('api/notifications/', include("notifications.urls")),
    path('api/operation/', include("operation.urls")),
    path('api/partners/', include("partners.urls")),
    path('api/products/', include("products.urls")),
    path('api/projects/', include("projects.urls")),
    path('api/purchasing/', include("purchasing.urls")),
    path('api/quotations/', include("quotations.urls")),
    path('api/risk/', include("risk.urls")),
    path("select2/", include("django_select2.urls")),
    path('api/subscriptions/', include("subscriptions.urls")),
    path('api/trade/', include("trade.urls")),
    path('api/underwriting/', include("underwriting.urls")),
    path('api/users/', include("users.urls")),
    
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    #path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('sentry-debug/', trigger_error),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)