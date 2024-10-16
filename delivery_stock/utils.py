from datetime import datetime
from delivery_stock.models import (
    DeliveryContainer, 
    ImageModel, Location,
    SecondRecDelivery
    )
import io
from reportlab.pdfgen import canvas

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import landscape, A4

import requests

from recive_stock.settings import CUPS_POST_URL

def get_transaction_reloc_str(from_loc, to_loc, request):
    return f"{datetime.now().strftime('%Y-%d-%m')} \
        Użytkownik {request.user.username} przeniósł kontener z lokalizacji \
            {from_loc} do lokalizacji {to_loc}"
def relocate_or_get_error(identifier, to_location, request):
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
        delivery_cont = DeliveryContainer.objects.get(identifier=identifier)
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
            
        if to_location == delivery_cont.location:
            del auto_in_val["to_location"]
            error_message = "Ta dostawa już jest w tej lokalizacji wybierz inną lokalizację"
            return {"status": False, "error_message": error_message} | auto_in_val
        
        # if to_location.work_zone == 4:
        #     delivery.complite_status = True
        delivery_cont.transaction += get_transaction_reloc_str(
            from_loc=delivery_cont.location.name,
            to_loc=to_location.name,
            request=request
        )
        delivery_cont.location = to_location
        delivery_cont.save()
        return {"status": status}
    return {"status": status, "error_message": error_message} | auto_in_val



def gen_pdf_recive_report(delivery):
    date_recive = delivery.date_recive.strftime("%Y.%m.%d")
    supplier = delivery.supplier_company.name
    warehous_adres = "Centrum Logistyczne Leroy Merlin ul. Łowicka 33 99-120 Piątek"
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
    
    my_canvas.drawString(50, 665, f"{date_recive}")
    my_canvas.drawString(150, 610, f"{recive_person}")
    my_canvas.drawString(40, 560, f"{supplier}")
    my_canvas.setFont("FreeSans", 8)
    my_canvas.drawString(270, 560, f"{warehous_adres}")
    my_canvas.setFont("FreeSans", 12)
    my_canvas.drawString(36, 444, "X")
    my_canvas.drawString(40, 290, f"{qty_unit}")
    my_canvas.drawString(140, 290, f"{recive_unit}")
    my_canvas.setFont("FreeSans", 10)
    my_canvas.drawString(220, 290, reasone_comment)

    my_canvas.showPage()
    my_canvas.save()
    buffer.seek(0)
    return buffer


def gen_damage_protocol(lines_info):
    damage_report_path = "static/reports/damage_protocol.jpg"

    buffer = io.BytesIO()
    pdfmetrics.registerFont(TTFont("FreeSans", "freesans/FreeSans.ttf"))
    my_canvas = canvas.Canvas(buffer)
    my_canvas = canvas.Canvas(buffer, pagesize=landscape(A4))
    my_canvas.drawImage(damage_report_path, 0, 0, width=840, height=602)
    my_canvas.setFont("FreeSans", 10)

    coordinate_Y = 354
    
    my_canvas.drawString(90, 440, f"{lines_info[0]['date_complite']}")
    my_canvas.drawString(170, 178, f"{lines_info[0]['date_complite']}")
    for line in lines_info:
        my_canvas.drawString(50, coordinate_Y, f"{line['sku']}")
        my_canvas.drawString(142, coordinate_Y, line["description"][:25])
        my_canvas.drawString(300, coordinate_Y, f"{line['qty']}")
        my_canvas.drawString(350, coordinate_Y, line["recive_unit"])
        my_canvas.drawString(450, coordinate_Y, line["preadvice"])
        my_canvas.drawString(530, coordinate_Y, line['supplier'][:20])
        my_canvas.drawString(690, coordinate_Y, f"{line['tir_nr']}")
        coordinate_Y -= 12

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

def get_line_info(line):
    if line.suplier_sku:
        return f"SKU: {line.suplier_sku.sku} QTY: {line.qty_unit} Jednostka: {line.recive_unit} & Description: {line.suplier_sku.deskription}"
    return f"QTY: {line.qty_unit} Jednostka: {line.recive_unit} &EAN: {line.not_sys_barcode}"


def print_labels(delivery_id):
    try:
        second_rec_delivery = (
            SecondRecDelivery.objects
            .select_related('supplier_company', 'user')
            .prefetch_related('deliverycontainer_set__containerline_set') 
            .get(id=delivery_id)
        )

        containers_info = []
        delivery_part = 1
        deliverycontainer_set = second_rec_delivery.deliverycontainer_set.all()
        for container in deliverycontainer_set:
            container_info = {
                "supplier_company": str(second_rec_delivery.supplier_company),
                "user": second_rec_delivery.user.username,
                "data": second_rec_delivery.date_recive.strftime("%Y/%m/%d"),
                "pre_advice": second_rec_delivery.pre_advice_nr,
                "master_id": second_rec_delivery.master_nr,
                "identifier": container.identifier,
                "delivery_part": f"{delivery_part}/{len(deliverycontainer_set)}",
                "lines_info": []
            }
            delivery_part += 1
            for line in container.containerline_set.all():
                line_info = {
                    "label_title": f"Line {line.line_nr}: {line.reasone_comment}",
                    "line_info": get_line_info(line),
                }
                container_info["lines_info"].append(line_info)

            containers_info.append(container_info)
        try:
            requests.post(CUPS_POST_URL, json=containers_info)
        except TimeoutError:
            pass
        
    except SecondRecDelivery.DoesNotExist:
        return {"error": f"No delivery found with ID {delivery_id}"}
    

def get_transaction_cont_creat_str(request):
    return f"{datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} Użytkownik {request.user.username} utworzył nowy container\n"

def get_transaction_line_add_str(request, line_position):
    return f"{datetime.now().strftime('%Y-%d-%m')} Użytkownik {request.user.username} dodał nową linię {line_position} do kontenera \n"