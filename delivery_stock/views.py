from datetime import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import View

from recive_stock.settings import GS_BUCKET_NAME
from .models import Delivery, ImageModel, Location, ReasoneComment, Supplier, SuplierSKU

from django.db import IntegrityError, transaction
from django.db.models import Q


class HomeView(LoginRequiredMixin, View):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
def admin_panel(request):
    return render(request, "delivery_stock/admin_panel.html")


class SelectReceptionView(LoginRequiredMixin, View):
    template_name = "delivery_stock/select_reception.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    

class DeliveryFirsrRecCreateView(LoginRequiredMixin, View):
    template_name = "delivery_stock/delivery_first_rec_create.html"

    def get_context_data(self, **kwargs):
        context = {}
        supliers_list = Supplier.objects.all()
        suppliers = [
            {"id": sup.id, "name": f"{sup.name} - {sup.supplier_wms_id}"}
            for sup in supliers_list
        ]
        context["recive_units"] = [ unit[0] for unit in Delivery.RECIVE_UNIT]
        reasones_list = ReasoneComment.objects.filter(reception="first")
        reasones = [{"id": reas.id, "name": reas.name} for reas in reasones_list]
        context["suppliers"] = suppliers
        context["reasones"] = reasones
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        supplier_id = request.POST.get("selected_supplier_id", None)
        pre_advice = request.POST.get("pre_advice", None)
        tape_of_unit = request.POST.get("tape_of_unit", None)
        qty = request.POST.get("qty_unit", None)
        ean = request.POST.get("ean", None)
        reason = request.POST.get("reasones")
        extra_comment = request.POST.get("extra_comment", "")
        date_recive = datetime.now()
        recive_lock, _ = Location.objects.get_or_create(name="1R-STOCK", work_zone=1)

        with transaction.atomic():
            delivery = Delivery.objects.create(
                supplier_company=get_object_or_404(Supplier, id=supplier_id),
                pre_advice_nr=pre_advice,
                reasone_comment=reason,
                user=self.request.user,
                recive_location=recive_lock,
                location=recive_lock,
                date_recive=date_recive,
                recive_unit=tape_of_unit,

            )
            delivery.save()
        return render(
            request, "delivery_stock/delivery_image_add.html", {"delivery_id": delivery.id}
        )
    
class DeliverySecondRecCreateView(LoginRequiredMixin, View):
    template_name = "delivery_stock/delivery_second_rec_create.html"

    def get_context_data(self, **kwargs):
        return {}

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        return render(
            request, "delivery/delivery_image_add.html", {"delivery_id": 1}
        )
    
class DeliveryImageAdd(LoginRequiredMixin, View):
    template_name = "delivery_stock/delivery_image_add.html"

    def get_context_data(self, **kwargs):
        context = {}
        return context

    def get(self, request, *args, **kwargs):
        delivery_id = int(self.request.GET.get("delivery_id"))
        back_to_detail = self.request.GET.get("back_to_detail")
        context = self.get_context_data()
        context["delivery_id"] = delivery_id
        context["back_to_detail"] = back_to_detail
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        delivery_id = self.request.POST.get("delivery_id")
        back_to_detail = self.request.POST.get("back_to_detail")
        print(back_to_detail)
        if request.FILES:
            delivery = Delivery.objects.get(id=delivery_id)
            index = 1
            images = []
            while f"images_url_{index}" in request.FILES:
                image_file = request.FILES[f"images_url_{index}"]
                images.append(
                    ImageModel(custom_prefix=delivery.pre_advice_nr, image_data=image_file)
                )
                index += 1
            image_instances = ImageModel.objects.bulk_create(images)
            delivery.images_url.add(*image_instances)
            delivery.save()
        if back_to_detail:
            return redirect("delivery_stock:delivery_detail", pk=delivery_id) 
        return render(request, "delivery_stock/select_reception.html")


class DeliveryStorageView(LoginRequiredMixin, View):
    template_name = "delivery_stock/storeg_filter_page.html"

    def get_context_data(self, **kwargs):
        context = {}
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}
        identifier = request.POST.get("identifier")
        pre_advice = request.POST.get("pre_advice")
        status = request.POST.get("status")
        date_recive = request.POST.get("date_recive")
        location = request.POST.get("location")
        recive_loc = request.POST.get("recive_loc")

        queryset = Delivery.objects.all().select_related(
            "supplier_company", "recive_location", "location"
        )

        if status and status != "None":
            queryset = queryset.filter(location__work_zone=status)
        if identifier and identifier != 'None':
            queryset = queryset.filter(identifier__icontains=identifier)
        if pre_advice and pre_advice != 'None':
            queryset = queryset.filter(nr_order=pre_advice)
        if date_recive and date_recive and date_recive != 'None':
            date_recive_dt = datetime.strptime(date_recive, "%Y-%m-%d")
            queryset = queryset.filter(date_recive__date=date_recive_dt)
        if location and location != 'None':
            queryset = queryset.filter(location__name__icontains=location)
        if recive_loc and recive_loc != 'None':
            queryset = queryset.filter(recive_location__name=recive_loc)

        page = request.POST.get('page', 1)
        paginator = Paginator(queryset.order_by("-date_recive"), 300)
        try:
            deliveries = paginator.page(page)
        except PageNotAnInteger:
            deliveries = paginator.page(1)
        except EmptyPage:
            deliveries = paginator.page(paginator.num_pages)

        context["delivery_list"] = deliveries
        context["filters"] = {
            "identifier": identifier,
            "pre_advice": pre_advice,
            "date_recive": date_recive,
            "status": status,
            "location": location,
            "recive_loc": recive_loc,
        }

        return render(request, "delivery_stock/delivery_list.html", context)

class DeleveryDetailView(LoginRequiredMixin, View):
    def get_context_data(self, delivery_id):
        context = {}
        delivery = get_object_or_404(Delivery, id=delivery_id)
        date_recive = delivery.date_recive.strftime("%d.%m.%Y")
        context["date_recive"] = date_recive

        if delivery.images_url.all():
            context["image_urls"] = []
            for url in delivery.images_url.all():
                image_path = (
                    f"https://storage.googleapis.com/{GS_BUCKET_NAME}/{url.image_data}"
                )
                context["image_urls"].append(image_path)
        context["delivery"] = delivery

        return context
    def get(self, request, *args, **kwargs):
        delivery_id = self.kwargs.get("pk")
        context = self.get_context_data(delivery_id=delivery_id)

        return render(request, "delivery_stock/delivery_detail.html", context)


class SupplierListView(LoginRequiredMixin, View):
    template_name = "delivery_stock/supplier_list.html"

    def get_context_data(self, **kwargs):
        context = {}
        suppliers = Supplier.objects.all()
        context["supplier_list"] = suppliers
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context=context)


class SupplierUpdateView(LoginRequiredMixin, View):
    template_name = "delivery_stock/supplier_update.html"

    def get_context_data(self, supplier_id):
        context = {}
        supplier = Supplier.objects.get(id=supplier_id)
        context["supplier"] = supplier
        return context

    def get(self, request, *args, **kwargs):
        supplier_id = self.kwargs.get("pk")
        context = self.get_context_data(supplier_id=supplier_id)
        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        supplier_id = self.kwargs.get("pk")
        wms_id = self.request.POST.get("wms_id")
        name = self.request.POST.get("sup_name")
        supplier = Supplier.objects.get(id=supplier_id)
        context = self.get_context_data(supplier_id=supplier_id)
        with transaction.atomic():
            try:
                if wms_id:
                    supplier.supplier_wms_id = wms_id
                if name:
                    supplier.name = name
                supplier.save()
            except IntegrityError as e:
                if "unique_supplier_wms_id" in str(e):
                    context["error_message"] = (
                        "Supplier with this WMS ID already exists"
                    )
                else:
                    context["error_message"] = (
                        "An error occurred while saving the supplier"
                    )
                return render(request, self.template_name, context)

        return redirect(reverse("delivery_stock:supplier_list"))


class SupplierCreateView(LoginRequiredMixin, View):
    template_name = "delivery_stock/supplier_create.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        wms_id = self.request.POST.get("wms_id")
        name = self.request.POST.get("sup_name")
        context = {"error_message": ""}
        with transaction.atomic():
            try:
                supplier = Supplier(name=name, supplier_wms_id=wms_id)
                supplier.save()
            except IntegrityError as e:
                if "unique_supplier_wms_id" in str(e):
                    context["error_message"] = (
                        "Supplier with this WMS ID already exists"
                    )
                else:
                    context["error_message"] = (
                        "An error occurred while saving the supplier"
                    )
                return render(request, self.template_name, context)

        return redirect(reverse("delivery_stock:supplier_list"))


class LocationListView(LoginRequiredMixin, View):
    template_name = "delivery_stock/location_list.html"
    def get_context_data(self, **kwargs):
        context = {}
        locations = Location.objects.all()
        context["location_list"] = locations
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context=context)


class LocationUpdateView(LoginRequiredMixin, View):
    template_name = "delivery_stock/location_update.html"

    def get_context_data(self, locatio_id):
        context = {}
        location = Location.objects.get(id=locatio_id)
        context["location"] = location
        return context 

    def get(self, request, *args, **kwargs):
        location_id = self.kwargs.get("pk")
        context = self.get_context_data(locatio_id=location_id)
        return render(request, self.template_name, context=context) 
    
    def post(self, request, *args, **kwargs):
        location_id = self.kwargs.get("pk")
        location_name = self.request.POST.get("location_name")
        work_zone = self.request.POST.get("work_zone")
        delete_status = self.request.POST.get("delete")
        context = self.get_context_data(locatio_id=location_id)
        context["error_message"] = ""
        
        location = Location.objects.get(id=location_id)

        if location.name in ["1R", "2R", "Shiped", "Utulizacja"]:
            context["error_message"] = "Ta lokalizacja jest ważna, nie można jej usunąć ani zmienić"
            return render(request, self.template_name, context)

        if delete_status:
            if len(Delivery.objects.filter(location=location))>0:
                context["error_message"] ="Ta lokalizacja nie jest pusta, wykonaj relokację"
                return render(request, self.template_name, context)
            location.delete()
            return redirect(reverse("delivery:location_list"))

        if location_name and location_name != location.name:
            location.name = location_name
        
        if work_zone and work_zone != location.work_zone:
            location.work_zone = work_zone
        location.save()
        return redirect(reverse("delivery:location_list"))


class LocationCreateView(LoginRequiredMixin, View):
    template_name = "delivery_stock/location_create.html"

    def get_context_data(self):
        context = {}
        context["WORKZON_CHOICES"] = Location.WORKZON_CHOICES
        return context 

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context=context) 

    def post(self, request, *args, **kwargs):
        location_name = self.request.POST.get("location_name")
        work_zone = self.request.POST.get("work_zone")
        context = self.get_context_data()
        try:
            Location.objects.create(
                name=location_name,
                work_zone=work_zone
            )
        except IntegrityError as e:
                context["error_message"] = (
                    "ta lokalizacja już istnieje"
                )
                return render(request, self.template_name, context=context) 

        return redirect(reverse("delivery:location_list"))
    

class SuplierSKUListView(LoginRequiredMixin, View):
    template_name = "delivery_stock/sku_list.html"

    def get_context_data(self, **kwargs):
        pass

    def get(self, request, *args, **kwargs):
        queryset = SuplierSKU.objects.all()
        page = request.GET.get("page", 1)
        paginator = Paginator(queryset.order_by("sku"), 300)

        filter_value = request.GET.get("filter", None)
        if filter_value:
            queryset = queryset.filter(Q(sku__contains=filter_value) | Q(barcode__icontains=filter_value))

        page = request.GET.get("page", 1)
        paginator = Paginator(queryset.order_by("sku"), 2)        
        try:
            sku_list = paginator.page(page)
        except PageNotAnInteger:
            sku_list = paginator.page(1)
        except EmptyPage:
            sku_list = paginator.page(paginator.num_pages)
        context = {}
        context["sku_list"] = sku_list
        return render(request, "delivery_stock/sku_list.html", context)
    def post(self, request, *args, **kwargs):
        return redirect(reverse("delivery_stock:sku_list"))


class SuplierSKUCreateView(LoginRequiredMixin, View):
    template_name = "delivery_stock/sku_create.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        sku = int(self.request.POST.get("sku"))
        barcode = self.request.POST.get("barcode")
        deskription = self.request.POST.get("deskription")
        context = {"error_message": ""}
        with transaction.atomic():
            try:
                suplier_sku = SuplierSKU(
                    sku=sku, barcode=barcode, deskription=deskription
                    )
                suplier_sku.save()
            except IntegrityError as e:
                if "unique_barcode" in str(e):
                    context["error_message"] = (
                        "Sku with this barcode already exists"
                    )
                else:
                    context["error_message"] = (
                        "An error occurred while saving the sku"
                    )
                return render(request, self.template_name, context)

        return redirect(reverse("delivery_stock:sku_list"))
    

class SuplierSKUUpdateView(LoginRequiredMixin, View):
    template_name = "delivery_stock/sku_update.html"

    def get_context_data(self, sku_id):
        context = {}
        suplier_sku = SuplierSKU.objects.get(id=sku_id)
        context["suplier_sku"] = suplier_sku
        return context
    
    def get(self, request, *args, **kwargs):
        sku_id = self.kwargs.get("pk")
        context = self.get_context_data(sku_id)
        return render(request, self.template_name, context=context)
    
    def post(self, request, *args, **kwargs):
        suplier_sku_id = self.kwargs.get("pk")
        sku = int(self.request.POST.get("sku", "1"))
        barcode = self.request.POST.get("barcode")
        deskription = self.request.POST.get("deskription")
        context = {"error_message": ""}
        delete_status = self.request.POST.get("delete")

        suplier_sku = SuplierSKU.objects.get(id=suplier_sku_id)
        if delete_status:
            if len(Delivery.objects.filter(suplier_sku=suplier_sku)) > 0 :
                context["error_message"] = "To SKU jest używane w Delivery, najpierw usuń Delivery."
                return render(request, self.template_name, context)
            suplier_sku.delete()
            return redirect(reverse("delivery_stock:sku_list"))
        
        if sku and sku != suplier_sku.sku:
            suplier_sku.sku = sku

        if barcode and barcode != suplier_sku.barcode:
            suplier_sku.barcode = barcode
        
        if deskription and deskription != suplier_sku.deskription:
            suplier_sku.deskription = deskription
        suplier_sku.save()
        return redirect(reverse("delivery_stock:sku_list"))
    