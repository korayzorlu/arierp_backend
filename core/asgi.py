"""
ASGI config for marswide_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter, get_default_application
from channels.security.websocket import AllowedHostsOriginValidator



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

django_asgi_app = get_asgi_application()

from users.routing import websocket_urlpatterns as user_websocket_urlpatterns

websocket_urlpatterns = user_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    ),
})