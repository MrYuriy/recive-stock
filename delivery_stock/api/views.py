from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from delivery_stock.models import SuplierSKU
from .serializers import SuplierSKUSerializer


class SuplierSKUByBarcode(APIView):
    def get(self, request, barcode):
        try:
            sku_instance = SuplierSKU.objects.filter(barcode__icontains=barcode).first()
            serializer = SuplierSKUSerializer(sku_instance)
            if not serializer.data["sku"]:
                return Response(
                {"error": "SKU not found"}, status=status.HTTP_404_NOT_FOUND
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SuplierSKU.DoesNotExist:
            return Response(
                {"error": "SKU not found"}, status=status.HTTP_404_NOT_FOUND
            )
