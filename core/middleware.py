from django.contrib.auth import logout
import ldap
import logging

import threading
from django.conf import settings

_user = threading.local()

def get_current_user():
    return getattr(_user, 'user', None)

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.user = request.user  # Request'teki kullanıcıyı yakalıyoruz
        response = self.get_response(request)
        return response

_thread_locals = threading.local()

def get_current_request():
    return getattr(_thread_locals, 'request', None)

class CurrentRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        return response
    
# class LDAPHealthCheckMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         user = get_current_user()
#         if user.is_authenticated:

            

#             try:
#                 conn = ldap.initialize("ldap://192.168.82.45:389")
#                 conn.simple_bind_s("sophos.central@arileasing.local", "Nowayout5057.*")
#                 user_data = conn.search_s(
#                     "dc=arileasing,dc=local",
#                     ldap.SCOPE_SUBTREE,
#                     f"(sAMAccountName={user.username})"
#                 )
#                 print(f"userd data: {user_data}")
#             except ldap.LDAPError:
#                 logout(request)
#         return self.get_response(request)

