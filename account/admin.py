from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmployeeProfile


# --------- Custom User Admin ---------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('id', 'email', 'full_name', 'role','latitude', 'longitude', 'otp', 'is_staff', 'is_active', 'is_verified')
    list_filter = ('role', 'is_staff', 'is_active', 'is_verified')
    ordering = ('email',)
    search_fields = ('email', 'full_name', 'role')

    # Since username is removed, update fieldsets accordingly
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone', 'location','latitude', 'otp', 'longitude', 'profile_image')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'latitude', 'longitude', 'otp','password1', 'password2', 'is_staff', 'is_active')}
        ),
    )



# --------- EmployeeProfile Admin ---------
@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'experience', 'hourly_rate', 'available')
    search_fields = ('user__full_name', 'title')
    list_filter = ('available',)
