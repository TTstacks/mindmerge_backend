from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User

# Register your models here.
class BaseAdmin(UserAdmin):
    list_display = ['email', 'is_admin']
    list_filter = ['is_admin']
    fieldsets = [
        (
            None,
            {
                "fields": ["email", "is_admin"]
            }
        )
    ]
    add_fieldsets = [
        (
            None,
            {
                "fields": ["email", "is_admin", "password1", "password2"]
            }
        ),
    ]
    ordering = ["email"]
    search_fields = ["email"]
    filter_horizontal = []

admin.site.register(User, BaseAdmin)