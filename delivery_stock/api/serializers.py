from rest_framework import serializers
from delivery_stock.models import SuplierSKU


class SuplierSKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuplierSKU
        fields = ["sku", "deskription", "barcode"]
