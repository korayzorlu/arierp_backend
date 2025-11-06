from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from subscriptions.models import *

class MenuItemListSerializer(serializers.Serializer):
    subscription = serializers.CharField(source = "department")
    menu_items = serializers.SerializerMethodField()
    
    def get_menu_items(self, obj):
        menu_items = [
            {"type" : "item", "class" : ["default"], "label" : "Kontrol Paneli", "icon" : "dashboard", "route" : "/dashboard"},
            {"type" : "sub_menu", "class" : ["admin"], "label" : "Organizasyon", "icon" : "organization", "items" : [
                {"type" : "item", "class" : ["admin"], "label" : "Firmalar", "icon" : "badge", "route" : "/companies"},
                {"type" : "item", "class" : ["admin"], "label" : "Davetiyeler", "icon" : "mail", "route" : "/invitations"}
            ]},
            {"type" : "sub_menu", "class" : ["default"], "label" : "Partner", "icon" : "handshake", "items" : [
                {"type" : "item", "class" : ["default"], "label" : "Partnerler", "icon" : "handshake", "route" : "/partners"},
                {"type" : "item", "class" : ["default"], "label" : "Tüketici Müşteriler", "icon" : "handshake", "route" : "/tuketici-partners"},
                {"type" : "item", "class" : ["default"], "label" : "Ticari Müşteriler", "icon" : "handshake", "route" : "/ticari-partners"},
                {"type" : "item", "class" : ["default"], "label" : "Sektörler", "icon" : "tree", "route" : "/sectors"},
            ]},
            {"type" : "sub_menu", "class" : ["default"], "label" : "Gayrimenkul", "icon" : "home_work", "items" : [
                {"type" : "item", "class" : ["default"], "label" : "Projeler", "icon" : "article", "route" : "/projects"},
                {"type" : "item", "class" : ["default"], "label" : "Parseller", "icon" : "article", "route" : "/parcels"},
                {"type" : "item", "class" : ["default"], "label" : "Taşınmazlar", "icon" : "article", "route" : "/real-estates"},
                {"type" : "item", "class" : ["default"], "label" : "Arı Leasing Tapular", "icon" : "article", "route" : "/title-deeds"},
            ]},
            {"type" : "sub_menu", "class" : ["default"], "label" : "Teklif", "icon" : "unknown", "items" : [
                {"type" : "item", "class" : ["default"], "label" : "Hızlı Teklifler", "icon" : "article", "route" : "/quick-quotations"},
                {"type" : "item", "class" : ["default"], "label" : "Teklifler", "icon" : "article", "route" : "/quotations"},
            ]},
            {"type" : "item", "class" : ["default"], "label" : "Sözleşmeler", "icon" : "description", "route" : "/contracts"},
            {"type" : "sub_menu", "class" : ["default"], "label" : "Kira Planı", "icon" : "unknown", "items" : [
                {"type" : "item", "class" : ["default"], "label" : "Kira Planları", "icon" : "description", "route" : "/leases"},
                {"type" : "item", "class" : ["default"], "label" : "Yürürlükteki Kira Planları", "icon" : "description", "route" : "/active-leases"},
                {"type" : "item", "class" : ["default"], "label" : "Kira Planları Detaylı", "icon" : "description", "route" : "/installments"},
            ]},
            # {"type" : "sub_menu", "class" : ["admin"], "label" : "Gayrimenkul", "icon" : "in_home_mode", "items" : [
            #     {"type" : "item", "class" : ["admin"], "label" : "Tapu Gayrimenkulleri", "icon" : "paid", "route" : "/krs-notifications"},
            # ]},
            # {"type" : "sub_menu", "class" : ["admin"], "label" : "Tahsis", "icon" : "policy", "items" : [
            #     {"type" : "item", "class" : ["admin"], "label" : "KRS Bildirimi", "icon" : "paid", "route" : "/krs-notifications"},
            #     {"type" : "item", "class" : ["admin"], "label" : "PEP Listesi", "icon" : "paid", "route" : "/pep-list"},
            # ]},
            {"type" : "sub_menu", "class" : ["default"], "label" : "Uyum", "icon" : "policy", "items" : [
                {"type" : "item", "class" : ["default"], "label" : "Sakıncalı Müşteri Listesi", "icon" : "paid", "route" : "/black-list-persons"},
                {"type" : "item", "class" : ["default"], "label" : "Kişi Sorgulama", "icon" : "paid", "route" : "/scan-partners"},
                {"type" : "item", "class" : ["default"], "label" : "3. Şahıs Ödemeleri", "icon" : "paid", "route" : "/third-persons"},
            ]},
            {"type" : "sub_menu", "class" : ["default"], "label" : "Operasyon", "icon" : "hub", "items" : [
                {"type" : "item", "class" : ["default"], "label" : "Müşteri Avansları", "icon" : "description", "route" : "/partner-advances"},
                {"type" : "item", "class" : ["operasyon"], "label" : "Müşteri Avansı İşleme", "icon" : "description", "route" : "/partner-advance-activities"},
                {"type" : "sub_menu", "class" : ["default"], "label" : "Sözleşme İzleme", "icon" : "description", "items" : [
                    {"type" : "item", "class" : ["default"], "label" : "Tedarikçide", "icon" : "paid", "route" : "/contract-in-suppliers"},
                    {"type" : "item", "class" : ["default"], "label" : "İşlemde", "icon" : "paid", "route" : "/contract-in-processs"},
                    {"type" : "item", "class" : ["default"], "label" : "Arşivde", "icon" : "paid", "route" : "/contract-in-archives"},
                ]},
            ]},
            {"type" : "sub_menu", "class" : ["default"], "label" : "Finans", "icon" : "paid", "items" : [
                {"type" : "item", "class" : ["finans"], "label" : "Banka Hesapları", "icon" : "description", "route" : "/bank-accounts"},
                {"type" : "item", "class" : ["finans"], "label" : "Banka Hesap Hareketleri", "icon" : "description", "route" : "/bank-account-transactions"},
                {"type" : "item", "class" : ["default"], "label" : "Tahsilatlar", "icon" : "paid", "route" : "/contract-payments"},
                {"type" : "item", "class" : ["finans"], "label" : "Tahsilat İşleme", "icon" : "paid", "route" : "/collections"},
                {"type" : "item", "class" : ["default"], "label" : "İşlenen Tahsilatlar", "icon" : "paid", "route" : "/bank-activities"},
                {"type" : "item", "class" : ["default"], "label" : "Satıcı Ödemeleri", "icon" : "description", "route" : "/purchase-payments"},
                {"type" : "item", "class" : ["default"], "label" : "Satıcı Ödemeleri Özet", "icon" : "description", "route" : "/finance-summary"},
                {"type" : "item", "class" : ["default"], "label" : "Statüsü Hatalı Olanlar", "icon" : "description", "route" : "/status-control"},
                {"type" : "item", "class" : ["default"], "label" : "Satın Alma Belgeleri", "icon" : "description", "route" : "/purchase-documents"},
                #{"type" : "item", "class" : ["default"], "label" : "Özet", "icon" : "description", "route" : "/finance-summary"},
            ]},
            {"type" : "sub_menu", "class" : ["default","operasyon"], "label" : "Risk", "icon" : "report", "items" : [
                {"type" : "sub_menu", "class" : ["default"], "label" : "Vadesi Geçmişler", "icon" : "description", "items" : [
                    {"type" : "item", "class" : ["default"], "label" : "Vadesi Geçmişler(Ham)", "icon" : "policy", "route" : "/overdue-leases"},
                    {"type" : "item", "class" : ["default"], "label" : "Gecikmede Olanlar(0-25)", "icon" : "policy", "route" : "/risk-partners"},
                    #{"type" : "item", "class" : ["default"], "label" : "İhtar Çekilecekler", "icon" : "policy", "route" : "/to-warned-risk-partners"},
                    {"type" : "item", "class" : ["default"], "label" : "İhtar Çekilecekler(Kapora)", "icon" : "policy", "route" : "/deposit-to-warned-risk-partners"},
                    {"type" : "item", "class" : ["default"], "label" : "İhtar Çekilecekler(Kep)", "icon" : "policy", "route" : "/kep-to-warned-risk-partners"},
                    {"type" : "item", "class" : ["default"], "label" : "İhtar Çekilecekler(Posta)", "icon" : "policy", "route" : "/posta-to-warned-risk-partners"},
                    {"type" : "item", "class" : ["default","operasyon"], "label" : "İhtar Çekilenler", "icon" : "policy", "route" : "/warned-risk-partners"},
                    {"type" : "item", "class" : ["default"], "label" : "Fesih Edilecekler", "icon" : "policy", "route" : "/to-terminated-risk-partners"},
                    {"type" : "item", "class" : ["default"], "label" : "Hatalı/Belirsiz Olanlar", "icon" : "policy", "route" : "/under-reviews"},
                    {"type" : "item", "class" : ["default"], "label" : "KDV Farkı Olanlar", "icon" : "policy", "route" : "/kdv-risk-partners"},
                ]},
                {"type" : "sub_menu", "class" : ["default"], "label" : "Vadesi Yaklaşanlar", "icon" : "description", "items" : [
                    {"type" : "item", "class" : ["default"], "label" : "Yarın Ödenecekler", "icon" : "policy", "route" : "/tomorrow-partners"},
                    {"type" : "item", "class" : ["default"], "label" : "Bugün Ödenecekler", "icon" : "policy", "route" : "/today-partners"},
                ]},
                {"type" : "sub_menu", "class" : ["default"], "label" : "SMS", "icon" : "description", "items" : [
                    {"type" : "item", "class" : ["default"], "label" : "Gönderilen SMS'ler", "icon" : "policy", "route" : "/sent-sms"},
                ]},
                {"type" : "sub_menu", "class" : ["default"], "label" : "Teslim", "icon" : "description", "items" : [
                    {"type" : "item", "class" : ["default"], "label" : "Teslim Onay", "icon" : "policy", "route" : "/delivery-confirm"},
                    {"type" : "item", "class" : ["default"], "label" : "Devredilecekler", "icon" : "policy", "route" : "/to-be-transferred"},
                ]},
                {"type" : "item", "class" : ["default"], "label" : "Kaporalar", "icon" : "policy", "route" : "/deposit-partners"},
                #{"type" : "item", "class" : ["default"], "label" : "1 Gün Gecikenler", "icon" : "policy", "route" : "/yesterday-partners"},
                {"type" : "item", "class" : ["default"], "label" : "İhtarlar", "icon" : "policy", "route" : "/warning-notices"},
                {"type" : "item", "class" : ["default"], "label" : "Anlaşmalı Fesihler", "icon" : "policy", "route" : "/agreed-terminated-partners"},
                {"type" : "item", "class" : ["default"], "label" : "Bakiye Temerrüt Raporu", "icon" : "policy", "route" : "/amount-debit-transaction"},
                {"type" : "item", "class" : ["default"], "label" : "Özet", "icon" : "policy", "route" : "/manager-summary"},
            ]},
            {"type" : "sub_menu", "class" : ["default"], "label" : "Muhasebe", "icon" : "checkbook", "items" : [
                # {"type" : "item", "class" : ["default"], "label" : "Muhasebe Hesapları", "icon" : "checkbook", "route" : "/ledger-accounts"},
                {"type" : "item", "class" : ["default"], "label" : "Genel Mizan", "icon" : "checkbook", "route" : "/trial-balances"},
            ]},
            {"type" : "sub_menu", "class" : ["default"], "label" : "Cari", "icon" : "price_change", "items" : [
                {"type" : "item", "class" : ["default"], "label" : "Cari Hesaplar", "icon" : "price_change", "route" : "/trade-accounts"},
                {"type" : "item", "class" : ["default"], "label" : "Cari Hesap Hareketleri", "icon" : "price_change", "route" : "/trade-transactions"},
            ]},
            # {"type" : "sub_menu", "class" : ["admin"], "label" : "Excel Dönüşümleri", "icon" : "accounting", "items" : [
            #     {"type" : "item", "class" : ["admin"], "label" : "Banka Hareketleri", "icon" : "account", "route" : "/banka-hareketleri"},
            #     {"type" : "item", "class" : ["admin"], "label" : "Banka Tahsilatları", "icon" : "account", "route" : "/banka-tahsilatlari"},
            #     {"type" : "item", "class" : ["admin"], "label" : "Banka Tahsilatları Odoo", "icon" : "account", "route" : "/banka--tahsilatlari-odoo"},
            # ]},
        ]

        hierarchy = {
            "admin": ["admin","bilgi_islem","default","finans","genel_mudurluk","ic_denetim","ic_kontrol","kredi_risk_izleme","kredi_tahsis","muhasebe","operasyon"],
            "bilgi_islem": ["default","bilgi_islem"],
            "default": ["default"],
            "finans": ["default","finans"],
            "genel_mudurluk": ["bilgi_islem","default","finans","genel_mudurluk","ic_denetim","ic_kontrol","kredi_risk_izleme","kredi_tahsis","muhasebe","operasyon"],
            "ic_denetim": ["default","ic_denetim"],
            "ic_kontrol": ["default","ic_kontrol"],
            "kredi_risk_izleme": ["default","kredi_risk_izleme"],
            "kredi_tahsis": ["default","kredi_tahsis"],
            "muhasebe": ["default","muhasebe","finans","genel_mudurluk","ic_denetim","ic_kontrol","kredi_risk_izleme","kredi_tahsis","operasyon"],
            "operasyon": ["default","operasyon"],
        }

        allowed_classes = hierarchy.get(obj.department, ["default"])
        print(allowed_classes)
        def filter_items(items):
            # return [item for item in items if item["class"] in allowed_classes]
            return [
                    item for item in items
                    if (
                        isinstance(item["class"], list)
                        and any(cls in allowed_classes for cls in item["class"])
                    ) or (
                        isinstance(item["class"], str)
                        and item["class"] in allowed_classes
                    )
                ]

        filtered_menu = []
        for menu in menu_items:
            if menu["type"] == "sub_menu":
                filtered_sub_items = filter_items(menu["items"])
                if filtered_sub_items:  # Eğer alt item kalmazsa, sub_menu'yu da ekleme
                    menu["items"] = filtered_sub_items
                    filtered_menu.append(menu)
            elif menu["type"] == "item":
                if (
                    isinstance(menu["class"], list)
                    and any(cls in allowed_classes for cls in menu["class"])
                ) or (
                    isinstance(menu["class"], str)
                    and menu["class"] in allowed_classes
                ):
                    filtered_menu.append(menu)


        return filtered_menu
