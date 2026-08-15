from datetime import date
from django.db.models import Exists, Q, OuterRef
from itertools import groupby
from backend.apps.hostels.models import Bed, Hostel
from backend.apps.allocations.models import BedAllocation

class AnalyticsService:
    @classmethod
    def _get_base_beds_queryset(cls, start_date: date, end_date: date, hostel_id: int = None, room_id: int = None):
        """
        Returns a queryset of Bed records, annotated with an `is_occupied` boolean
        based on active BedAllocations that overlap the given date range.
        """
        overlapping_allocations = Q(
            is_active=True,
            start_date__lte=end_date,
            end_date__gte=start_date
        )

        beds = Bed.objects.select_related('room', 'room__floor__block__hostel')

        if hostel_id:
            beds = beds.filter(room__floor__block__hostel_id=hostel_id)
        if room_id:
            beds = beds.filter(room_id=room_id)

        # Ensure we count physical beds properly and don't duplicate rows
        # Exists creates a subquery that evaluates to True if at least one allocation matches
        return beds.annotate(
            is_occupied=Exists(
                BedAllocation.objects.filter(bed=OuterRef('pk')).filter(overlapping_allocations)
            )
        )

    @classmethod
    def get_hostel_utilization(cls, start_date: date, end_date: date, hostel_id: int = None, threshold: float = 0.50) -> list[dict]:
        beds = cls._get_base_beds_queryset(start_date, end_date, hostel_id=hostel_id)
        
        # Group by Hostel in Python to avoid complex SQL grouping
        # We need to sort by hostel id to use groupby effectively
        beds_list = sorted(beds, key=lambda b: (b.room.floor.block.hostel.id, b.room.id))
        
        results = []
        for h_id, hostel_beds_iter in groupby(beds_list, key=lambda b: b.room.floor.block.hostel.id):
            hostel_beds = list(hostel_beds_iter)
            hostel = hostel_beds[0].room.floor.block.hostel
            
            total_beds = len(hostel_beds)
            occupied_beds = sum(1 for b in hostel_beds if b.is_occupied)
            vacant_beds = total_beds - occupied_beds
            
            # Distinct rooms
            total_rooms = len(set(b.room.id for b in hostel_beds))
            
            occupancy_rate = occupied_beds / total_beds if total_beds > 0 else 0.0
            vacancy_rate = vacant_beds / total_beds if total_beds > 0 else 0.0
            utilization_rate = occupancy_rate
            underutilized = (utilization_rate < threshold) if total_beds > 0 else False

            results.append({
                "hostel_id": hostel.id,
                "hostel_name": hostel.name,
                "total_rooms": total_rooms,
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "vacant_beds": vacant_beds,
                "occupancy_rate": round(occupancy_rate, 4),
                "vacancy_rate": round(vacancy_rate, 4),
                "utilization_rate": round(utilization_rate, 4),
                "underutilized": underutilized
            })
            
        # If a specific hostel was requested but has no beds, it won't show up in the groupby
        # Let's ensure empty hostels are included if a specific hostel_id is provided
        if hostel_id and not results:
            try:
                hostel = Hostel.objects.get(id=hostel_id)
                results.append({
                    "hostel_id": hostel.id,
                    "hostel_name": hostel.name,
                    "total_rooms": 0,
                    "total_beds": 0,
                    "occupied_beds": 0,
                    "vacant_beds": 0,
                    "occupancy_rate": 0.0,
                    "vacancy_rate": 0.0,
                    "utilization_rate": 0.0,
                    "underutilized": False
                })
            except Hostel.DoesNotExist:
                pass
                
        return results

    @classmethod
    def get_room_utilization(cls, start_date: date, end_date: date, hostel_id: int = None, room_id: int = None, threshold: float = 0.50) -> list[dict]:
        beds = cls._get_base_beds_queryset(start_date, end_date, hostel_id=hostel_id, room_id=room_id)
        
        # Sort by room_id for grouping
        beds_list = sorted(beds, key=lambda b: b.room.id)
        
        results = []
        for r_id, room_beds_iter in groupby(beds_list, key=lambda b: b.room.id):
            room_beds = list(room_beds_iter)
            room = room_beds[0].room
            hostel = room.floor.block.hostel
            
            total_beds = len(room_beds)
            occupied_beds = sum(1 for b in room_beds if b.is_occupied)
            vacant_beds = total_beds - occupied_beds
            
            occupancy_rate = occupied_beds / total_beds if total_beds > 0 else 0.0
            vacancy_rate = vacant_beds / total_beds if total_beds > 0 else 0.0
            utilization_rate = occupancy_rate
            underutilized = (utilization_rate < threshold) if total_beds > 0 else False

            results.append({
                "room_id": room.id,
                "room_number": room.room_number,
                "hostel_name": hostel.name,
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "vacant_beds": vacant_beds,
                "occupancy_rate": round(occupancy_rate, 4),
                "vacancy_rate": round(vacancy_rate, 4),
                "utilization_rate": round(utilization_rate, 4),
                "underutilized": underutilized
            })
            
        return results
