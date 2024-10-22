from django.urls import path
from .views import SuplierSKUByBarcode

urlpatterns = [
    path(
        "supplier-sku/<str:barcode>/",
        SuplierSKUByBarcode.as_view(),
        name="supplier-sku-by-barcode",
    ),
]
