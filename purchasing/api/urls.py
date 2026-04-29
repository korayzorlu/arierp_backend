from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'purchase_payments',PurchasePaymentList, "purchase_payments_api")
router.register(r'purchase_payment_vendors',PurchasePaymentVendorList, "purchase_payment_vendors_api")
router.register(r'purchase_documents',PurchaseDocumentList, "purchase_documents_api")
router.register(r'purchase_document_items',PurchaseDocumentItemList, "purchase_document_items_api")
router.register(r'purchase_document_vendors',PurchaseDocumentVendorList, "purchase_document_vendors_api")

urlpatterns = [
    path('',include(router.urls)),
]
