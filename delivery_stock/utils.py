from delivery_stock.models import Delivery, Location


def relocate_or_get_error(identifier, to_location, *args, **kwargs):
    ereor_message = ""
    status = True
    auto_in_val = {"identifier": identifier, "to_location": to_location}
   
    try:
        to_location = Location.objects.get(name__iexact=to_location)
    except Location.DoesNotExist:
        error_message = "Nieprawidłowa lokalizacja"
        del auto_in_val["to_location"]
        status = False
    try:
        delivery = Delivery.objects.get(identifier=identifier)
    except Delivery.DoesNotExist:
        if error_message:
            error_message += "i identyfikator."
        else:
            error_message = "Nieprawidłowy identyfikator."
        del auto_in_val["identifier"]
        status = False

    if status:
        if delivery.complite_status:
            del auto_in_val["to_location"]
            del auto_in_val["identifier"]
            error_message = "Zamówienie ma status complete"
            return {"status": False, "error_message": error_message} | auto_in_val
            
        if to_location == delivery.location:
            del auto_in_val["to_location"]
            error_message = "Ta dostawa już jest w tej lokalizacji wybierz inną lokalizację"
            return {"status": False, "error_message": error_message} | auto_in_val
        
        if to_location.work_zone == 4:
            delivery.complite_status = True

        delivery.location = to_location
        delivery.save()
        return {"status": status}
    return {"status": status, "error_message": error_message} | auto_in_val
