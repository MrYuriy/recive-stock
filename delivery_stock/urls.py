from django.urls import path

from delivery_stock.views import (
    DeleveryFirsRecDetailView,
    DeliveryFirsrRecCreateView, 
    DeliveryImageAddView, 
    DeliverySecondRecCreateView,
    DeliveryContainerView,
    ContainerLineView,
    DeliveryStorSecondRecView,
    DeliveryStorageView,
    DeliveryStorFirstRecView, 
    HomeView,
    LocationCreateView,
    LocationListView,
    LocationUpdateView,
    RelocationView, SelectReceptionView,
    SelectStoreReceptionView,
    SuplierSKUCreateView,
    SupplierCreateView,
    SupplierListView,
    SupplierUpdateView,
    SuplierSKUListView,
    SuplierSKUUpdateView,
    admin_panel,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("reception/", SelectReceptionView.as_view(), name="select_receprion"),
    path("store-reception/", SelectStoreReceptionView.as_view(), name="select_store_receprion"),
    path("first-rec/create/", DeliveryFirsrRecCreateView.as_view(), name="first_rec_del_create"),
    path("second-rec/create/", DeliverySecondRecCreateView.as_view(), name="second_rec_del_create"),
    path("add-delivery-container/", DeliveryContainerView.as_view(), name="add_delivery_cont"),
    path("add-container-line/", ContainerLineView.as_view(), name="add_cont_line"),
    path("add-image/", DeliveryImageAddView.as_view(), name="add_image"),
    path("storage/", DeliveryStorageView.as_view(), name="delivery_storage"),
    path("storage-f-rec/", DeliveryStorFirstRecView.as_view(), name="store_first_rec"),
    path("storage-s-rec/", DeliveryStorSecondRecView.as_view(), name="store_second_rec"),
    path("<int:pk>/detail/", DeleveryFirsRecDetailView.as_view(), name="delivery_f_rec_detail"),
    path("admin-panel/", admin_panel, name="admin_panel"),
    path("supplier-list/", SupplierListView.as_view(), name="supplier_list"),
    path("supplier-create/", SupplierCreateView.as_view(), name="supplier_create"),
    path(
        "<int:pk>/supplier-update/",
        SupplierUpdateView.as_view(),
        name="supplier_update",
    ),
    path("location-list/", LocationListView.as_view(), name="location_list"),
    path("location-create/", LocationCreateView.as_view(), name="location_create"),
    path(
        "<int:pk>/location-update/",
        LocationUpdateView.as_view(),
        name="location_update"
        ),
    path("sku-list/", SuplierSKUListView.as_view(), name="sku_list"),
    path("sku-create/", SuplierSKUCreateView.as_view(), name="sku_create"),
    path(
        "<int:pk>/sku-update/",
        SuplierSKUUpdateView.as_view(),
        name="sku_update"
        ),
    path("relocation/", RelocationView.as_view(), name="delivery_relocation"),

]

app_name = "delivery_stock"