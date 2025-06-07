from rest_framework.permissions import BasePermission
from django.http import JsonResponse
from django.shortcuts import render, redirect

class SubscriptionPermission(BasePermission):
    subscription_hierarchy = {
        "free": ["free"],
        "standart": ["free", "standart"],
        "premium": ["free", "standart", "premium"],
        "enterprise": ["free", "standart", "premium", "enterprise"]
    }

    def has_permission(self, request, view):
        try:
            user_subscription = request.user.subscription.type
            required_subscription = getattr(view, "required_subscription", "free")

            allowed_subscriptions = self.subscription_hierarchy.get(user_subscription, ["free"])
            return required_subscription in allowed_subscriptions
        except:
            return None

class BlockBrowserAccessPermission(BasePermission):
    def has_permission(self, request, view):
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        requested_with = request.headers.get("X-Requested-With", "").lower()
        
        if "mozilla" in user_agent or "chrome" in user_agent or "safari" in user_agent or "edge" in user_agent:
            if requested_with == "xmlhttprequest":
                return True
            return False

        return True
    
class RequireCustomHeaderPermission(BasePermission):
    def has_permission(self, request, view):
        return request.headers.get("X-Requested-With") == "XMLHttpRequest"