from django.contrib import admin
from .models import ApplicationBatch, StudentApplication, Preference

@admin.register(ApplicationBatch)
class ApplicationBatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'batch', 'status', 'created_at')
    list_filter = ('status', 'batch', 'created_at')
    search_fields = ('student__registration_number', 'student__user__username')
    autocomplete_fields = ('student',)

@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ('application', 'preferred_room_type', 'preferred_ac', 'budget_tier')
    list_filter = ('preferred_room_type', 'preferred_ac', 'budget_tier')
    autocomplete_fields = ('application', 'roommate_requests')
