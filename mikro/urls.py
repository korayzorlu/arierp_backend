from django.urls import path, include

from .views import *

app_name = "mikro"

urlpatterns = [
    path('set_vpn/', SetVpnView.as_view(), name="set_vpn"),
    path('get_vpn_status/', GetVpnStatusView.as_view(), name="get_vpn_status"),
    
    path('api/', include("mikro.api.urls")),
]