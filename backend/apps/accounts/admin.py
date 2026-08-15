from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Role', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Role', {'fields': ('role',)}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'user', 'department', 'course_year', 'gender')
    list_filter = ('department', 'course_year', 'gender')
    search_fields = ('registration_number', 'user__username', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user',)
