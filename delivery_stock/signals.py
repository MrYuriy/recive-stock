from datetime import datetime
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import DeliveryContainer, FirstRecDelivery, SecondRecDelivery
import uuid


@receiver(pre_save, sender=DeliveryContainer)
@receiver(pre_save, sender=SecondRecDelivery)
@receiver(pre_save, sender=FirstRecDelivery)
def generate_delivery_number(sender, instance, **kwargs):
    unik_id = str(uuid.uuid4())
    unik_id = "".join(filter(str.isdigit, unik_id))
    now = datetime.now()
    if not instance.identifier:
        instance.identifier = int(now.strftime("%Y%m%d")[2:] + unik_id[-6:])
