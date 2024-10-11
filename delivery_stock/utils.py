from delivery_stock.models import (
    DeliveryContainer, 
    ImageModel, Location
    )
import io
from reportlab.pdfgen import canvas

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def relocate_or_get_error(identifier, to_location, *args, **kwargs):
    error_message = ""
    status = True
    auto_in_val = {"identifier": identifier, "to_location": to_location}
   
    try:
        to_location = Location.objects.get(name__iexact=to_location)
    except Location.DoesNotExist:
        error_message = "Nieprawidłowa lokalizacja"
        del auto_in_val["to_location"]
        status = False
    try:
        delivery = DeliveryContainer.objects.get(identifier=identifier)
    except DeliveryContainer.DoesNotExist:
        if error_message:
            error_message += " i identyfikator."
        else:
            error_message = "Nieprawidłowy identyfikator."
        del auto_in_val["identifier"]
        status = False

    if status:
        # if delivery.complite_status:
        #     del auto_in_val["to_location"]
        #     del auto_in_val["identifier"]
        #     error_message = "Zamówienie ma status complete"
        #     return {"status": False, "error_message": error_message} | auto_in_val
            
        if to_location == delivery.location:
            del auto_in_val["to_location"]
            error_message = "Ta dostawa już jest w tej lokalizacji wybierz inną lokalizację"
            return {"status": False, "error_message": error_message} | auto_in_val
        
        # if to_location.work_zone == 4:
        #     delivery.complite_status = True

        delivery.location = to_location
        delivery.save()
        return {"status": status}
    return {"status": status, "error_message": error_message} | auto_in_val



def gen_pdf_recive_report(delivery):
    date_recive = delivery.date_recive.strftime("%Y-%m-%d")
    supplier = delivery.supplier_company.name
    warehous_adres = "Centrum Logistyczne Leroy Merlin\nul. Łowicka 33\n99-120 Piątek"
    recive_person = delivery.user.full_name
    recive_unit = delivery.recive_unit
    qty_unit = delivery.qty_unit
    reasone_comment = f"Podczas rozładunku stwierdzono {delivery.reasone_comment}"

    recive_report_path = "static/reports/recive_report.jpg"

    buffer = io.BytesIO()
    pdfmetrics.registerFont(TTFont("FreeSans", "freesans/FreeSans.ttf"))
    my_canvas = canvas.Canvas(buffer)
    my_canvas.drawImage(recive_report_path, 0, 0, width=602, height=840)
    my_canvas.setFont("FreeSans", 10)


    my_canvas.showPage()
    my_canvas.save()
    buffer.seek(0)
    return buffer


def save_images_for_object(request, obj, prefix):
        index = 1
        images = []
        while f"images_url_{index}" in request.FILES:
            image_file = request.FILES[f"images_url_{index}"]
            images.append(ImageModel(custom_prefix=prefix, image_data=image_file))
            index += 1
        if images:
            image_instances = ImageModel.objects.bulk_create(images)
            obj.images_url.add(*image_instances)
            obj.save()