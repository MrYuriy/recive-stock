from django.contrib import admin

from .models import (
    ReasoneComment,
    Location,
    SuplierSKU,
    Supplier,
    SecondRecDelivery,
    ImageModel,
    FirstRecDelivery,
    DeliveryContainer,
    ContainerLine,
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


class ContainerLineAdmin(admin.ModelAdmin):
    list_display = (
        "line_nr",
        "container",
        "suplier_sku",
        "not_sys_barcode",
        "recive_unit",
        "qty_unit",
    )
    search_fields = ("not_sys_barcode", "suplier_sku__sku", "container__identifier")
    list_filter = ("recive_unit", "container")

    raw_id_fields = ("suplier_sku",)

    filter_horizontal = ("images_url",)


admin.site.register(Location)
admin.site.register(SuplierSKU)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(FirstRecDelivery, FirstRecDeliveryAdmin)
admin.site.register(ReasoneComment)
admin.site.register(ImageModel)
admin.site.register(SecondRecDelivery, SecondRecDeliveryAdmin)
admin.site.register(DeliveryContainer)
admin.site.register(ContainerLine, ContainerLineAdmin)
