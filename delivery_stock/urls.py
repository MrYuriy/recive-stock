from django.urls import path

from delivery_stock.views import (
    DeleveryDetailView,
    DeliveryFirsrRecCreateView, 
    DeliveryImageAdd, 
    DeliverySecondRecCreateView,
    DeliveryStorageView, 
    HomeView, SelectReceptionView
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("reception/", SelectReceptionView.as_view(), name="select_receprion"),
    path("first-rec/create/", DeliveryFirsrRecCreateView.as_view(), name="first_rec_del_create"),
    path("second-rec/create/", DeliverySecondRecCreateView.as_view(), name="second_rec_del_create"),
    path("add-image/", DeliveryImageAdd.as_view(), name="add_image"),
    path("storage/", DeliveryStorageView.as_view(), name="delivery_storage"),
    path("<int:pk>/detail/", DeleveryDetailView.as_view(), name="delivery_detail"),
]

app_name = "delivery_stock"