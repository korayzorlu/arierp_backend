from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from subscriptions.models import *

class MenuItemListSerializer(serializers.Serializer):
    subscription = serializers.CharField(source = "type")
    menu_items = serializers.SerializerMethodField()
    
    def get_menu_items(self, obj):
        menu_items = [
            {"type" : "item", "class" : "free", "label" : "Kontrol Paneli", "icon" : "dashboard", "route" : "/dashboard"},
            {"type" : "sub_menu", "class" : "free", "label" : "Organizasyon", "icon" : "organization", "items" : [
                {"type" : "item", "class" : "free", "label" : "Firmalar", "icon" : "badge", "route" : "/companies"},
                {"type" : "item", "class" : "free", "label" : "Davetiyeler", "icon" : "mail", "route" : "/invitations"}
            ]},
            {"type" : "sub_menu", "class" : "free", "label" : "Partner", "icon" : "handshake", "items" : [
                {"type" : "item", "class" : "free", "label" : "Partnerler", "icon" : "handshake", "route" : "/partners"},
                {"type" : "item", "class" : "free", "label" : "Sektörler", "icon" : "tree", "route" : "/sectors"},
            ]},
            {"type" : "item", "class" : "free", "label" : "Projeler", "icon" : "home_work", "route" : "/projects"},
            {"type" : "sub_menu", "class" : "free", "label" : "Teklif", "icon" : "unknown", "items" : [
                {"type" : "item", "class" : "free", "label" : "Hızlı Teklifler", "icon" : "article", "route" : "/quick-quotations"},
                {"type" : "item", "class" : "free", "label" : "Teklifler", "icon" : "article", "route" : "/quotations"},
            ]},
            {"type" : "item", "class" : "free", "label" : "Sözleşmeler", "icon" : "description", "route" : "/contracts"},
            {"type" : "sub_menu", "class" : "free", "label" : "Kira Planı", "icon" : "unknown", "items" : [
                {"type" : "item", "class" : "free", "label" : "Kira Planları", "icon" : "description", "route" : "/leases"},
                {"type" : "item", "class" : "free", "label" : "Kira Planları Detaylı", "icon" : "description", "route" : "/installments"},
            ]},
            {"type" : "sub_menu", "class" : "free", "label" : "Tahsilat", "icon" : "paid", "items" : [
                {"type" : "item", "class" : "free", "label" : "Tahsilatlar", "icon" : "paid", "route" : "/contract-payments"},
                {"type" : "item", "class" : "free", "label" : "Tahsilat İşleme", "icon" : "paid", "route" : "/collections"},
                {"type" : "item", "class" : "free", "label" : "İşlenen Tahsilatlar", "icon" : "paid", "route" : "/collectionss"},
            ]},
            {"type" : "sub_menu", "class" : "free", "label" : "Satın Alma", "icon" : "real_estate_agent", "items" : [
                {"type" : "item", "class" : "free", "label" : "Satıcı Ödemeleri", "icon" : "description", "route" : "/purchase-payments"},
            ]},
            {"type" : "sub_menu", "class" : "free", "label" : "Risk", "icon" : "policy", "items" : [
                {"type" : "item", "class" : "free", "label" : "Risk İzleme(Ham)", "icon" : "policy", "route" : "/overdue-leases"},
                {"type" : "item", "class" : "free", "label" : "Vadesi Geçmişler", "icon" : "policy", "route" : "/risk-partners"},
                {"type" : "item", "class" : "free", "label" : "İhtar Çekilecekler", "icon" : "policy", "route" : "/to-warned-risk-partners"},
                {"type" : "item", "class" : "free", "label" : "İhtar Çekilenler", "icon" : "policy", "route" : "/warned-risk-partners"},
                {"type" : "item", "class" : "free", "label" : "Fesih Edilecekler", "icon" : "policy", "route" : "/to-terminated-risk-partners"},
                {"type" : "item", "class" : "free", "label" : "KDV Farkı Olanlar", "icon" : "policy", "route" : "/kdv-risk-partners"},
                {"type" : "item", "class" : "free", "label" : "Yarın Ödenecekler", "icon" : "policy", "route" : "/tomorrow-partners"},
                {"type" : "item", "class" : "free", "label" : "Bugün Ödenecekler", "icon" : "policy", "route" : "/today-partners"},
                {"type" : "item", "class" : "free", "label" : "Kaporalar", "icon" : "policy", "route" : "/deposit-partners"},
                #{"type" : "item", "class" : "free", "label" : "1 Gün Gecikenler", "icon" : "policy", "route" : "/yesterday-partners"},
                {"type" : "item", "class" : "free", "label" : "İhtarlar", "icon" : "policy", "route" : "/warning-notices"},
                {"type" : "item", "class" : "free", "label" : "Teslim Onay", "icon" : "policy", "route" : "/delivery-confirm"},
                #{"type" : "item", "class" : "free", "label" : "Yönetici Özeti", "icon" : "policy", "route" : "/summary"},
            ]},
            {"type" : "sub_menu", "class" : "free", "label" : "Muhasebe", "icon" : "checkbook", "items" : [
                {"type" : "item", "class" : "free", "label" : "Muhasebe Hesapları", "icon" : "checkbook", "route" : "/ledger-accounts"},
            ]},
            {"type" : "sub_menu", "class" : "free", "label" : "Cari", "icon" : "price_change", "items" : [
                {"type" : "item", "class" : "free", "label" : "Cari Hesaplar", "icon" : "price_change", "route" : "/trade-accounts"},
            ]},
            # {"type" : "sub_menu", "class" : "free", "label" : "Excel Dönüşümleri", "icon" : "accounting", "items" : [
            #     {"type" : "item", "class" : "free", "label" : "Banka Hareketleri", "icon" : "account", "route" : "/banka-hareketleri"},
            #     {"type" : "item", "class" : "free", "label" : "Banka Tahsilatları", "icon" : "account", "route" : "/banka-tahsilatlari"},
            #     {"type" : "item", "class" : "free", "label" : "Banka Tahsilatları Odoo", "icon" : "account", "route" : "/banka--tahsilatlari-odoo"},
            # ]},
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
