from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

from django.contrib.sessions.models import Session
from django.contrib.admin import ModelAdmin



User = get_user_model()

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class UserAdmin(UserAdmin):
    model = User
    list_display = (
        "username",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
    )
    list_filter = ("is_active", "is_staff", "is_superuser")
    fieldsets = (
        (None, {"fields": ("username", "email", "password", "full_name", "role","force_password_change")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "full_name",
                    "email",
                    "role",
                    "force_password_change",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)

class SessionAdmin(ModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()
    list_display = ['session_key', '_session_data', 'expire_date']
admin.site.register(Session, SessionAdmin)