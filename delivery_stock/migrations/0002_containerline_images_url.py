# Generated by Django 5.1.1 on 2024-10-09 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("delivery_stock", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="containerline",
            name="images_url",
            field=models.ManyToManyField(blank=True, to="delivery_stock.imagemodel"),
        ),
    ]
