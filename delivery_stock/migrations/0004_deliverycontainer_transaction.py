# Generated by Django 5.1.1 on 2024-10-16 04:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("delivery_stock", "0003_containerline_line_nr"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliverycontainer",
            name="transaction",
            field=models.TextField(blank=True, null=True),
        ),
    ]