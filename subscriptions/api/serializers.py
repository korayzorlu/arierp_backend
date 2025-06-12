from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from subscriptions.models import *

class MenuItemListSerializer(serializers.Serializer):
    subscription = serializers.CharField(source = "type")
    menu_items = serializers.SerializerMethodField()
    
    def get_menu_items(self, obj):
        menu_items = [
            {"type" : "item", "class" : "free", "label" : "Dashboard", "icon" : "dashboard", "route" : "/dashboard"},
            {"type" : "sub_menu", "class" : "free", "label" : "Organizations", "icon" : "organization", "items" : [
                {"type" : "item", "class" : "free", "label" : "Companies", "icon" : "badge", "route" : "/companies"},
                {"type" : "item", "class" : "free", "label" : "Invitations", "icon" : "mail", "route" : "/invitations"}
            ]},
            # {"type" : "item", "class" : "free", "label" : "Partners", "icon" : "dashboard", "route" : "/partners"},
            {"type" : "sub_menu", "class" : "free", "label" : "Excel Dönüşümleri", "icon" : "accounting", "items" : [
                {"type" : "item", "class" : "free", "label" : "Banka Hareketleri", "icon" : "account", "route" : "/banka-hareketleri"},
                {"type" : "item", "class" : "free", "label" : "Banka Tahsilatları", "icon" : "account", "route" : "/banka-tahsilatlari"},
                {"type" : "item", "class" : "free", "label" : "Banka Tahsilatları Odoo", "icon" : "account", "route" : "/banka--tahsilatlari-odoo"},
            ]},
        ]

        hierarchy = {
            "free": ["free"],
            "standart": ["free", "standart"],
            "premium": ["free", "standart", "premium"],
            "enterprise": ["free", "standart", "premium", "enterprise"]
        }

        allowed_classes = hierarchy.get(obj.type, ["free"])

        def filter_items(items):
            return [item for item in items if item["class"] in allowed_classes]

        filtered_menu = []
        for menu in menu_items:
            if menu["type"] == "sub_menu":
                filtered_sub_items = filter_items(menu["items"])
                if filtered_sub_items:  # Eğer alt item kalmazsa, sub_menu'yu da ekleme
                    menu["items"] = filtered_sub_items
                    filtered_menu.append(menu)
            elif menu["type"] == "item":
                if menu["class"] in allowed_classes:
                    filtered_menu.append(menu)


        return filtered_menu
