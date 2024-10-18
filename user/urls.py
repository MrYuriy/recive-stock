from django.urls import path

from user.views import CustomPasswordChangeView, UserCreateView, UserDeleteView, UserListView, UserUpdateView

urlpatterns = [
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/create/", UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/update/", UserUpdateView.as_view(), name="user-update"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="user-delete"),
    path('password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
]

app_name = "user"
