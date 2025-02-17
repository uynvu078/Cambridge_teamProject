from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'status', 'is_staff')

    def get_model_perms(self, request):
        """Move 'Users' before 'Email Addresses' by returning True"""
        return {'add': True, 'change': True, 'delete': True}

    def get_app_label(self):
        """Custom app label to control order"""
        return "A_Users"  
