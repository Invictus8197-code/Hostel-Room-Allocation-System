from django.contrib import admin
from .models import AllocationRun, BedAllocation

@admin.register(AllocationRun)
class AllocationRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'run_date', 'status', 'fairness_score')
    list_filter = ('status', 'run_date')
    search_fields = ('id', 'status')

@admin.register(BedAllocation)
class BedAllocationAdmin(admin.ModelAdmin):
    list_display = ('student', 'bed', 'allocation_run', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'allocation_run', 'start_date', 'end_date')
    search_fields = ('student__registration_number', 'bed__bed_number')
    autocomplete_fields = ('student', 'bed', 'allocation_run')
