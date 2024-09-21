# Generated by Django 5.1.1 on 2024-09-21 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Delivery",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("identifier", models.BigIntegerField(unique=True)),
                ("pre_advice_nr", models.CharField(max_length=40, null=True)),
                ("reasone_comment", models.TextField()),
                ("date_recive", models.DateTimeField()),
                (
                    "recive_unit",
                    models.CharField(
                        choices=[
                            ("szt.", "szt."),
                            ("pall.", "pall"),
                            ("pacz.", "pacz."),
                        ],
                        max_length=10,
                    ),
                ),
                ("transaction", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=20, unique=True)),
                (
                    "work_zone",
                    models.IntegerField(
                        choices=[
                            (1, "Recive"),
                            (2, "Storage"),
                            (3, "Ready to load"),
                            (4, "Utilization"),
                            (4, "Shiped"),
                            (4, "Cancel"),
                            (4, "Transfer"),
                        ],
                        default=1,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ReasoneComment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "reception",
                    models.CharField(
                        choices=[("first", "first"), ("srcond", "second")],
                        max_length=10,
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="SuplierSKU",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("sku", models.IntegerField()),
                ("deskription", models.CharField(max_length=200)),
                ("barcode", models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Supplier",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=70)),
                ("supplier_wms_id", models.CharField(max_length=40)),
            ],
        ),
    ]