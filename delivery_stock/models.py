from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from recive_stock import settings


class ReasoneComment(models.Model):
    RECEPTIONS_CHOISES = [
        ("first", "first"),
        ("srcond", "second"),
    ]
    reception = models.CharField(choices=RECEPTIONS_CHOISES, max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


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

    RECIVE_UNIT = [
        ("szt.", "szt."),
        ("pall.", "pall"),
        ("pacz.", "pacz.")
    ]

    identifier = models.BigIntegerField(unique=True)
    supplier_company = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    pre_advice_nr = models.CharField( max_length=40, null=True)
    reasone_comment = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recive_location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="recive_location"
    )
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="location"
    )
    date_recive = models.DateTimeField()
    recive_unit = models.CharField(choices=RECIVE_UNIT, max_length=10)
    transaction = models.TextField(blank=True) 
    #Img_link field

    def __str__(self):
        return str(self.pre_advice_nr)
    