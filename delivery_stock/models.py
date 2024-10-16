from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from recive_stock import settings
from datetime import datetime
from google.cloud import storage
import os
import uuid

class ReasoneComment(models.Model):
    RECEPTIONS_CHOISES = [
        ("first", "first"),
        ("second", "second"),
    ]
    reception = models.CharField(choices=RECEPTIONS_CHOISES, max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name
    
def custom_upload_path(instance, filename):
    main_path = datetime.now().strftime("%Y/%m/%d/")
    syfix_name = (datetime.now().strftime("%H%M%S")) + f"{uuid.uuid4()}"
    filename, file_extension = os.path.splitext(filename)
    return f"{main_path}{instance.custom_prefix}_{syfix_name}{file_extension}"


class ImageModel(models.Model):
    custom_prefix = models.CharField(max_length=50, blank=True)
    image_data = models.ImageField(upload_to=custom_upload_path)

    def __str__(self):
        return self.new_filename()  # Call the method to get the new filename

    def new_filename(self):
        return os.path.basename(self.image_data.name)

    def delete(self, *args, **kwargs):
        self.delete_image_from_bucket()
        super().delete(*args, **kwargs)

    def delete_image_from_bucket(self):
        bucket_name = settings.GS_BUCKET_NAME
        file_path = str(self.image_data)
        credentials = settings.GS_CREDENTIALS
        client = storage.Client(credentials=credentials)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        blob.delete()


class Location(models.Model):

    WORKZON_ONE = 1
    WORKZON_TWO = 2
    WORKZON_THREE = 3
    WORKZON_FOR = 4

    WORKZON_CHOICES = (
        (WORKZON_ONE, "Recive"),
        (WORKZON_TWO, "Storage"),
        (WORKZON_THREE, "Ready to load"),
        (WORKZON_FOR, "Utilization"),
        (WORKZON_FOR, "Shiped"),
        (WORKZON_FOR, "Cancel"),
        (WORKZON_FOR, "Transfer"),
    )
    DEFAULT_WORK_ZONE = WORKZON_ONE

    name = models.CharField(max_length=20, unique=True)
    work_zone = models.IntegerField(choices=WORKZON_CHOICES, default=DEFAULT_WORK_ZONE)

    def __str__(self) -> str:
        return self.name

class SuplierSKU(models.Model):
    sku = models.IntegerField()
    deskription = models.CharField(max_length=200)
    barcode = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return (f"{self.sku} - {self.deskription}")
    

class Supplier(models.Model):
    name = models.CharField(max_length=70)
    supplier_wms_id = models.CharField(max_length=40)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "supplier_wms_id"], name="unique_supplier_wms_id"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.supplier_wms_id}"

class Delivery(models.Model):
    identifier = models.BigIntegerField(unique=True)
    supplier_company = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_recive = models.DateTimeField()
    date_complite = models.DateTimeField(null=True , blank=True)


    def __str__(self):
        return str(self.identifier)
    

class FirstRecDelivery(Delivery):
    RECIVE_UNIT = [
        ("szt.", "szt."),
        ("pall.", "pall"),
        ("pacz.", "pacz."),
    ]
    
    qty_unit = models.IntegerField()
    recive_unit = models.CharField(choices=RECIVE_UNIT, max_length=10)
    images_url = models.ManyToManyField(ImageModel, blank=True)
    tir_nr = models.CharField(max_length=40)
    container_nr = models.CharField(max_length=40, null=True, blank=True)
    reasone_comment = models.TextField()
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="location",
        null=True, blank=True
    )
    recive_location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="recive_location"
    )



class SecondRecDelivery(Delivery):
    pre_advice_nr = models.CharField(max_length=40, null=True , blank=True)
    master_nr = models.CharField(max_length=40, null=True, blank=True)
    tir_nr = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        return f"{self.identifier} {self.pre_advice_nr} {self.tir_nr}"


class DeliveryContainer(models.Model):
    identifier = models.BigIntegerField(unique=True)
    recive_location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="recive_location_2r"
    )
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="location_2r"
    )
    lovo_link = models.TextField(blank=True, null=True)
    lovo_name = models.TextField(blank=True, null=True)
    delivery = models.ForeignKey(SecondRecDelivery, on_delete=models.CASCADE)
    date_complite = models.DateTimeField(null=True , blank=True)
    transaction = models.TextField(blank=True, null=True, default="")

    def __str__(self) -> str:
        return f"{self.identifier} {self.delivery.identifier}"
    

class ContainerLine(models.Model):
    RECIVE_UNIT = [
        ("szt.", "szt."),
        ("pall. mix.", "pall. mix."),
        ("pall.full.", "pall.full."),
        ("pacz.", "pacz."),
    ]

    reasone_comment = models.TextField()
    qty_unit = models.IntegerField()
    recive_unit = models.CharField(choices=RECIVE_UNIT, max_length=10)
    not_sys_barcode = models.CharField(max_length=40, blank=True, null=True)
    suplier_sku = models.ForeignKey(
        SuplierSKU, on_delete=models.CASCADE, blank=True, null=True
    )
    container = models.ForeignKey(DeliveryContainer, on_delete=models.CASCADE)
    images_url = models.ManyToManyField(ImageModel, blank=True)
    line_nr = models.IntegerField(default=1)


    def __str__(self) -> str:
        return f"{self.suplier_sku.sku if self.suplier_sku else self.not_sys_barcode} {self.container.identifier}"

