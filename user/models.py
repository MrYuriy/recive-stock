from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    USER_ROLE_CHOICES = (
        ("admin", "Admin"),
        ("leader", "Leader"),
        ("regular", "Regular User"),
    )

    role = models.CharField(max_length=10, choices=USER_ROLE_CHOICES, default="regular")
    full_name = models.CharField(max_length=100, blank=True)
    force_password_change = models.BooleanField(default=False)

    # Avoid reverse accessor clashes with related_name
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",  # Unique related_name to avoid conflict
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions_set",  # Unique related_name to avoid conflict
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse("user:user-list")
