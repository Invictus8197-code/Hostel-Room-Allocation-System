from django.contrib import admin
from .models import Hostel, Block, Floor, Room, Bed

@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender_type')
    list_filter = ('gender_type',)
    search_fields = ('name',)

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostel')
    list_filter = ('hostel',)
    search_fields = ('name', 'hostel__name')

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('floor_number', 'block')
    list_filter = ('block__hostel', 'block')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'floor', 'room_type', 'is_ac')
    list_filter = ('room_type', 'is_ac', 'floor__block__hostel')
    search_fields = ('room_number',)

@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('bed_number', 'room')
    search_fields = ('bed_number', 'room__room_number')
    list_filter = ('room__floor__block__hostel',)
