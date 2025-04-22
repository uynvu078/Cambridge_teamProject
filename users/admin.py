from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Unit, Approver, Delegation
from .forms import ApproverForm

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'status', 'is_staff')

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('unit',),
        }),
    )

    def get_model_perms(self, request):
        return {'add': True, 'change': True, 'delete': True}

    def get_app_label(self):
        return "A_Users"

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name',)

@admin.register(Approver)
class ApproverAdmin(admin.ModelAdmin):
    form = ApproverForm
    list_display = ('user', 'unit', 'is_org_wide')
    list_filter = ('unit', 'is_org_wide')
    search_fields = ('user__username', 'user__email')

admin.site.register(Delegation)
