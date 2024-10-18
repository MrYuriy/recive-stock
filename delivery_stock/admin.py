from django.contrib import admin

from .models import (
    ReasoneComment, Location, 
    SuplierSKU, Supplier, SecondRecDelivery,
    ImageModel, FirstRecDelivery,
    DeliveryContainer, ContainerLine
    )


class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "supplier_wms_id")
    search_fields = ["supplier_wms_id"]


class FirstRecDeliveryAdmin(admin.ModelAdmin):
    list_display = ("identifier", "tir_nr", "container_nr")
    search_fields = ("identifier",)
    list_filter = ("identifier",)

class SecondRecDeliveryAdmin(admin.ModelAdmin):
    list_display = ("identifier", "pre_advice_nr", "master_nr")
    search_fields = ("identifier",)
    list_filter = ("identifier",)


admin.site.register(Location)
admin.site.register(SuplierSKU)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(FirstRecDelivery, FirstRecDeliveryAdmin)
admin.site.register(ReasoneComment)
admin.site.register(ImageModel)
admin.site.register(SecondRecDelivery, SecondRecDeliveryAdmin)
admin.site.register(DeliveryContainer)
admin.site.register(ContainerLine)
