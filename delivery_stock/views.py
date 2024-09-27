from datetime import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from recive_stock.settings import GS_BUCKET_NAME
from .models import Delivery, ImageModel, Location, ReasoneComment, Supplier

from django.db import IntegrityError, transaction


class HomeView(LoginRequiredMixin, View):
    template_name = "index.html"

    # write_report_gs()
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


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

