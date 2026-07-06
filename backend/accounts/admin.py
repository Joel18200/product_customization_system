from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Unregister the default and re-register with customizations
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Enhanced User admin with additional list display fields."""
    list_display = [
        "username", "email", "first_name", "last_name",
        "is_active", "is_staff", "date_joined",
    ]
    list_filter = ["is_active", "is_staff", "is_superuser", "date_joined"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["-date_joined"]
