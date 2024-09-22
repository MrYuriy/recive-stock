from django.contrib import admin

from .models import (
    ReasoneComment, Location, 
    SuplierSKU, Supplier, Delivery,
    ImageModel
    )


class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "supplier_wms_id")
    search_fields = ["supplier_wms_id"]


class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("identifier", "pre_advice_nr",)
    search_fields = ("identifier",)
    list_filter = ("identifier",)


admin.site.register(Location)
admin.site.register(SuplierSKU)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(ReasoneComment)
admin.site.register(ImageModel)
