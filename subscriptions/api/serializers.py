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
            {"type" : "item", "class" : "free", "label" : "Partners", "icon" : "handshake", "route" : "/partners"},
            {"type" : "sub_menu", "class" : "free", "label" : "Inventory", "icon" : "inventory", "items" : [
                {"type" : "item", "class" : "free", "label" : "Categories", "icon" : "tree", "route" : "/categories"},
                {"type" : "item", "class" : "free", "label" : "Products", "icon" : "box", "route" : "/products"}
            ]},
            {"type" : "sub_menu", "class" : "free", "label" : "Accounting", "icon" : "accounting", "items" : [
                {"type" : "item", "class" : "free", "label" : "Accounts", "icon" : "account", "route" : "/accounts"},
                {"type" : "item", "class" : "free", "label" : "Invoices", "icon" : "invoice", "route" : "/invoices"},
                {"type" : "item", "class" : "free", "label" : "Payments", "icon" : "payment", "route" : "/payments"}
            ]},
            {"type" : "sub_menu", "class" : "free", "label" : "Mikro", "icon" : "database", "items" : [
                {"type" : "item", "class" : "free", "label" : "Cari Hesap Hareketleri", "icon" : "home", "route" : "/cari-hesap-hareketleri"},
                {"type" : "item", "class" : "free", "label" : "Personeller", "icon" : "home", "route" : "/personeller"},
                {"type" : "item", "class" : "free", "label" : "Personel Tahakkukları", "icon" : "home", "route" : "/personel_tahakkuklari"}
            ]}
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
