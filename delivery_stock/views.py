from datetime import datetime
from django.http import FileResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import View

from delivery_stock.utils import do_repack, gen_damage_protocol, gen_pdf_recive_report, get_transaction_cont_creat_str, get_transaction_line_add_str, relocate_or_get_error, save_images_for_object, print_labels
from recive_stock.settings import GS_BUCKET_NAME
from .models import (
    ContainerLine,
    Delivery,
    DeliveryContainer,
    ImageModel,
    Location,
    ReasoneComment,
    SecondRecDelivery,
    Supplier,
    SuplierSKU,
    FirstRecDelivery,
)

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.db.models import Prefetch


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


class SelectStoreReceptionView(LoginRequiredMixin, View):
    template_name = "delivery_stock/select_store_reception.html"

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
        context["recive_units"] = [unit[0] for unit in FirstRecDelivery.RECIVE_UNIT]
        reasones_list = ReasoneComment.objects.filter(reception="first")
        reasones = [{"id": reas.id, "name": reas.name} for reas in reasones_list]
        context["suppliers"] = suppliers
        context["reasones"] = reasones
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        supplier_id = request.POST.get("selected_supplier_id")
        tape_of_unit = request.POST.get("tape_of_unit")
        qty = request.POST.get("qty_unit")
        reason = request.POST.get("reasones")
        tir_nr = request.POST.get("tir_nr")
        container_nr = request.POST.get("container_nr") or None
        date_recive = datetime.now()
        recive_lock = Location.objects.get(name="1R-STOCK", work_zone=1)

        with transaction.atomic():
            delivery = FirstRecDelivery.objects.create(
                supplier_company=get_object_or_404(Supplier, id=supplier_id),
                reasone_comment=reason,
                user=self.request.user,
                recive_location=recive_lock,
                location=recive_lock,
                date_recive=date_recive,
                recive_unit=tape_of_unit,
                qty_unit=qty,
                tir_nr=tir_nr,
                container_nr=container_nr,
            )
            delivery.save()
        return render(
            request,
            "delivery_stock/delivery_image_add.html",
            {
                "obj_id": delivery.id,
                "obj_model": "FirstRecDelivery",
            },
        )


class DeliverySecondRecCreateView(LoginRequiredMixin, View):
    template_name = "delivery_stock/delivery_second_rec_create.html"

    def get_context_data(self, **kwargs):
        context = {}
        supliers_list = Supplier.objects.all()
        suppliers = [
            {"id": sup.id, "name": f"{sup.name} - {sup.supplier_wms_id}"}
            for sup in supliers_list
        ]
        context["suppliers"] = suppliers
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        supplier_id = request.POST.get("selected_supplier_id", None)
        pre_advice = request.POST.get("pre_advice", None)
        master_nr = request.POST.get("master_nr")
        date_recive = datetime.now()
        recive_lock = Location.objects.get(name="2R-STOCK", work_zone=1)

        with transaction.atomic():
            delivery = SecondRecDelivery.objects.create(
                supplier_company=get_object_or_404(Supplier, id=supplier_id),
                pre_advice_nr=pre_advice,
                user=self.request.user,
                date_recive=date_recive,
                master_nr=master_nr,
            )
            delivery_cont = DeliveryContainer(
                location=recive_lock, delivery=delivery, recive_location=recive_lock
            )
            delivery_cont.transaction += get_transaction_cont_creat_str(request)
            delivery.save()
            delivery_cont.save()
            context = {}
            context["delivery_id"] = delivery.id
            context["delivery_cont_id"] = delivery_cont.id
        return redirect(
            reverse("delivery_stock:add_cont_line")
            + f"?delivery_id={delivery.id}&delivery_cont_id={delivery_cont.id}"
        )


class DeliveryContainerView(LoginRequiredMixin, View):
    template_name = "delivery_stock/add_delivery_container.html"

    def get(self, request, *args, **kwargs):
        delivery_id = request.GET.get("delivery_id")
        delivery_cont_id = request.GET.get("delivery_cont_id")
        context = {}
        context["delivery_id"] = delivery_id
        context["delivery_cont_id"] = delivery_cont_id
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        button_id = request.POST.get("button_id")
        delivery_id = request.POST.get("delivery_id")
        delivery_cont_id = request.POST.get("delivery_cont_id")

        if button_id == "add_line_btn":
            return redirect(
                reverse("delivery_stock:add_cont_line")
                + f"?delivery_id={delivery_id}&delivery_cont_id={delivery_cont_id}"
            )
        elif button_id == "add_container_btn":
            delivery = SecondRecDelivery.objects.get(id=delivery_id)
            rec_loc = Location.objects.get(name="2R-STOCK", work_zone=1)
            delivery_cont = DeliveryContainer(
                location=rec_loc, delivery=delivery, recive_location=rec_loc
            )
            delivery_cont.transaction += get_transaction_cont_creat_str(request)
            delivery_cont.save()
            return redirect(
                reverse("delivery_stock:add_cont_line")
                + f"?delivery_id={delivery.id}&delivery_cont_id={delivery_cont.id}"
            )
        elif button_id == "finish_btn":
            # do print labels here
            print_labels(delivery_id)
            return render(request, "delivery_stock/select_reception.html")


class ContainerLineView(LoginRequiredMixin, View):
    template_name = "delivery_stock/add_container_line.html"

    def get_context_data(self, **kwargs):
        context = {}

        context["recive_units"] = [unit[0] for unit in ContainerLine.RECIVE_UNIT]
        reasones_list = ReasoneComment.objects.filter(reception="second")
        reasones = [{"id": reas.id, "name": reas.name} for reas in reasones_list]

        context["reasones"] = reasones
        return context

    def get(self, request, *args, **kwargs):
        delivery_id = request.GET.get("delivery_id")
        delivery_cont_id = request.GET.get("delivery_cont_id")

        context = self.get_context_data()
        context["delivery_id"] = delivery_id
        context["delivery_cont_id"] = delivery_cont_id

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        delivery_id = request.POST.get("delivery_id")
        delivery_cont_id = request.POST.get("delivery_cont_id")

        unit_type = request.POST.get("tape_of_unit")
        qty = request.POST.get("qty_unit")
        ean = request.POST.get("ean")
        reason = request.POST.get("reasones")

        container = DeliveryContainer.objects.get(id=delivery_cont_id)
        line_position = container.containerline_set.count() + 1
        # create new container if current line is full. pallet
        if unit_type == "pall.full.":
            delivery_cont_id = ""
            if line_position >= 2:
                recive_loc = Location.objects.get(name="2R-STOCK", work_zone=1)
                container = DeliveryContainer(
                    location = recive_loc,
                    delivery = SecondRecDelivery.objects.get(id=delivery_id),
                    recive_location = recive_loc
                )
                line_position = 1
                container.transaction += get_transaction_cont_creat_str(request)
                container.save()
            
        supplier_sku = (
            SuplierSKU.objects.filter(barcode__icontains=ean).first()
            if ean != ""
            else None
        )
        cont_line = ContainerLine(
            reasone_comment=reason,
            qty_unit=qty,
            suplier_sku=supplier_sku,
            container=container,
            recive_unit=unit_type,
            line_nr=line_position,
            not_sys_barcode=ean if supplier_sku is None else None,
        )
        container.transaction += get_transaction_line_add_str(request, line_position)
        container.save()
        cont_line.save()
        if request.FILES:
            save_images_for_object(request, cont_line, container.id)
        return redirect(
            reverse("delivery_stock:add_delivery_cont")
            + f"?delivery_id={delivery_id}&delivery_cont_id={delivery_cont_id}"
        )


class DeliveryImageAddView(LoginRequiredMixin, View):
    template_name = "delivery_stock/image_add.html"

    def get_context_data(self, **kwargs):
        context = {}
        return context

    def get(self, request, *args, **kwargs):
        obj_id = self.request.GET.get("obj_id")
        obj_model = self.request.GET.get("obj_model")
        back_to_detail = self.request.GET.get("back_to_detail")

        context = self.get_context_data()
        context["obj_id"] = obj_id
        context["obj_model"] = obj_model
        context["back_to_detail"] = back_to_detail

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        obj_id = self.request.POST.get("obj_id")
        obj_model = self.request.POST.get("obj_model")
        back_to_detail = self.request.POST.get("back_to_detail")
        # Отримати модель динамічно
        ModelClass = globals().get(obj_model)

        if ModelClass is None:
            return HttpResponseBadRequest(f"Unknown model: {obj_model}")
        obj = ModelClass.objects.get(id=obj_id)

        if request.FILES:
            save_images_for_object(request, obj, obj.identifier)

        if back_to_detail:
            return redirect(f"{obj_model.lower()}_detail", pk=obj_id)
        return render(request, "delivery_stock/select_reception.html")


class DeliveryStorFirstRecView(LoginRequiredMixin, View):
    template_name = "delivery_stock/storeg_f_rec_filter_page.html"

    def get_context_data(self, **kwargs):
        context = {}
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}
        identifier = request.POST.get("identifier")
        status = request.POST.get("status")
        date_recive = request.POST.get("date_recive")
        location = request.POST.get("location")

        queryset = FirstRecDelivery.objects.all().select_related(
            "supplier_company", "location", "recive_location", "user"
        )

        if status and status != "None":
            queryset = queryset.filter(location__work_zone=status)
        if identifier and identifier != "None":
            queryset = queryset.filter(identifier__icontains=identifier)
        if date_recive and date_recive and date_recive != "None":
            date_recive_dt = datetime.strptime(date_recive, "%Y-%m-%d")
            queryset = queryset.filter(date_recive__date=date_recive_dt)
        if location and location != "None":
            queryset = queryset.filter(location__name__icontains=location)

        page = request.POST.get("page", 1)
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
            "date_recive": date_recive,
            "status": status,
            "location": location,
        }

        return render(request, "delivery_stock/delivery_f_rec_list.html", context)


class DeliveryStorSecondRecView(LoginRequiredMixin, View):
    template_name = "delivery_stock/storeg_s_rec_filter_page.html"

    def get_context_data(self, **kwargs):
        context = {}
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}
        identifier = request.POST.get("identifier")
        status = request.POST.get("status")
        date_recive = request.POST.get("date_recive")
        location = request.POST.get("location")

        queryset = ContainerLine.objects.select_related(
            "container",
            "container__delivery",
            "container__delivery__supplier_company",
            "suplier_sku",
        )

        if status and status != "None":
            queryset = queryset.filter(location__work_zone=status)
        if identifier and identifier != "None":
            queryset = queryset.filter(identifier__icontains=identifier)
        if date_recive and date_recive != "None":
            date_recive_dt = datetime.strptime(date_recive, "%Y-%m-%d")
            queryset = queryset.filter(
                container__delivery__date_recive__date=date_recive_dt
            )
        if location and location != "None":
            queryset = queryset.filter(location__name__icontains=location)

        page = request.POST.get("page", 1)
        paginator = Paginator(
            queryset.order_by("-container__delivery__date_recive"), 300
        )
        try:
            delivery_lines = paginator.page(page)
        except PageNotAnInteger:
            delivery_lines = paginator.page(1)
        except EmptyPage:
            delivery_lines = paginator.page(paginator.num_pages)

        context["line_list"] = delivery_lines
        context["filters"] = {
            "identifier": identifier,
            "date_recive": date_recive,
            "status": status,
            "location": location,
        }

        return render(request, "delivery_stock/delivery_s_rec_list.html", context)


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

        queryset = Delivery.objects.all().select_related("supplier_company")

        if status and status != "None":
            queryset = queryset.filter(location__work_zone=status)
        if identifier and identifier != "None":
            queryset = queryset.filter(identifier__icontains=identifier)
        if pre_advice and pre_advice != "None":
            queryset = queryset.filter(nr_order=pre_advice)
        if date_recive and date_recive and date_recive != "None":
            date_recive_dt = datetime.strptime(date_recive, "%Y-%m-%d")
            queryset = queryset.filter(date_recive__date=date_recive_dt)
        if location and location != "None":
            queryset = queryset.filter(location__name__icontains=location)
        if recive_loc and recive_loc != "None":
            queryset = queryset.filter(recive_location__name=recive_loc)

        page = request.POST.get("page", 1)
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


class DeleveryFirsRecDetailView(LoginRequiredMixin, View):
    def get_context_data(self, delivery_id):
        context = {}
        delivery = get_object_or_404(FirstRecDelivery, id=delivery_id)
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

        return render(request, "delivery_stock/delivery_f_rec_detail.html", context)


class ContainerDetailView(LoginRequiredMixin, View):
    def get_context(self, container_id):
        container = (
            DeliveryContainer.objects.select_related(
                "recive_location", "location", "delivery", "delivery__supplier_company"
            )
            .prefetch_related(
                Prefetch(
                    "containerline_set",
                    queryset=ContainerLine.objects.prefetch_related("images_url"),
                )
            )
            .get(id=container_id)
        )

        container_data = {
            "container_id": container_id,
            "identifier": container.identifier,
            "recive_location": container.recive_location.name,
            "location": container.location.name,
            "lovo_link": container.lovo_link,
            "lovo_name": container.lovo_name,
            "delivery_identifier": container.delivery.identifier,
            "pre_advice_nr": container.delivery.pre_advice_nr,
            "master_nr": container.delivery.master_nr,
            "tir_nr": container.delivery.tir_nr,
            "date_complite": container.date_complite,
            "transaction": container.transaction
        }

        lines_data = []
        for line in container.containerline_set.all():
            lines_data.append(
                {
                    "line_nr": line.line_nr,
                    "reasone_comment": line.reasone_comment,
                    "qty_unit": line.qty_unit,
                    "recive_unit": line.recive_unit,
                    "not_sys_barcode": line.not_sys_barcode,
                    "suplier_sku": line.suplier_sku.sku if line.suplier_sku else None,
                    "ean": line.suplier_sku.barcode if line.suplier_sku else None,
                    "deskription": line.suplier_sku.deskription if line.suplier_sku else None,
                    "images_url": [
                        f"https://storage.googleapis.com/{GS_BUCKET_NAME}/{image.image_data}"
                        for image in line.images_url.all()
                    ],
                }
            )

        container_data["container_lines"] = lines_data
        return container_data

    def get(self, request, *args, **kwargs):
        container_id = self.kwargs.get("pk")
        context = self.get_context(container_id)

        return render(request, "delivery_stock/container_detail.html", context)
    

    def post(self, request, *args, **kwargs):
        container_id = request.POST.get("container_id")
        if request.POST.get("add_tir_nr"):
                delivery = DeliveryContainer.objects.select_related('delivery').get(id=container_id).delivery
                delivery.tir_nr = request.POST.get("TIR_NR")
                delivery.save()
            

        return redirect("delivery_stock:container_detail", pk=container_id)


class DeliveryContainerRepacView(LoginRequiredMixin, View):
    template_name = "delivery_stock/delivery_container_repac.html"
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        context = do_repack(request)
        if context["status"]:
            return redirect("delivery_stock:repac_cont")
        else:
            print("Kurwa")
            return render(request, self.template_name, context)
        
        


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
            context["error_message"] = (
                "Ta lokalizacja jest ważna, nie można jej usunąć ani zmienić"
            )
            return render(request, self.template_name, context)

        if delete_status:
            if len(Delivery.objects.filter(location=location)) > 0:
                context["error_message"] = (
                    "Ta lokalizacja nie jest pusta, wykonaj relokację"
                )
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
            Location.objects.create(name=location_name, work_zone=work_zone)
        except IntegrityError as e:
            context["error_message"] = "ta lokalizacja już istnieje"
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
            queryset = queryset.filter(
                Q(sku__contains=filter_value) | Q(barcode__icontains=filter_value)
            )

        page = request.GET.get("page", 1)
        paginator = Paginator(queryset.order_by("sku"), 500)
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
                    context["error_message"] = "Sku with this barcode already exists"
                else:
                    context["error_message"] = "An error occurred while saving the sku"
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
            if len(Delivery.objects.filter(suplier_sku=suplier_sku)) > 0:
                context["error_message"] = (
                    "To SKU jest używane w Delivery, najpierw usuń Delivery."
                )
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


class RelocationView(LoginRequiredMixin, View):
    template_name = "delivery_stock/relocation.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        identifier = request.POST.get("identifier")
        to_location = request.POST.get("to_location")
        context = relocate_or_get_error(
            identifier=identifier, to_location=to_location, request=request
        )
        if context["status"]:
            return render(
                request,
                self.template_name,
            )
        else:
            return render(request, self.template_name, context)


def gen_first_rec_pdf_report(request):
    delivery_id = request.POST.get("delivery_id")

    delivery = FirstRecDelivery.objects.get(id=delivery_id)

    report = gen_pdf_recive_report(delivery)

    response = FileResponse(report, as_attachment=False, filename="Protokół szkody.pdf")
    return response


def gen_damage_pdf_protocol(request):
    container_id = request.POST.get("container_id")
    container = (
            DeliveryContainer.objects.select_related(
                "recive_location", "location", "delivery", "delivery__supplier_company"
            )
            .prefetch_related(
                Prefetch(
                    "containerline_set",
                    queryset=ContainerLine.objects.prefetch_related("images_url"),
                )
            )
            .get(id=container_id)
        )
    if not container.date_complite:
        container.date_complite = datetime.now()
        container.save()
    
    lines_info = []
    for line in container.containerline_set.all():
        line_info = {}
        line_info["sku"] = line.suplier_sku.sku if line.suplier_sku else line.not_sys_barcode
        line_info["description"] = line.suplier_sku.deskription if line.suplier_sku else " - - - - - -"
        line_info["qty"] = line.qty_unit
        line_info["recive_unit"] = line.recive_unit
        line_info["preadvice"] = container.delivery.pre_advice_nr
        line_info["supplier"] = container.delivery.supplier_company.name
        line_info["tir_nr"] = container.delivery.tir_nr
        line_info["date_complite"] = container.date_complite.strftime("%Y.%m.%d")
        
        lines_info.append(line_info)
    report = gen_damage_protocol(lines_info)
    response = FileResponse(report, as_attachment=False, filename="Protokół szkody.pdf")
    return response
