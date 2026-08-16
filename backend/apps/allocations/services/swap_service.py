from backend.apps.allocations.models import BedAllocation
from backend.apps.applications.models import Preference
from django.db import transaction

class SwapService:
    @staticmethod
    def find_cycles(batch_id):
        # A simple algorithm to find 2-way swaps (A wants B's room, B wants A's room)
        # For a hackathon, a 2-way cycle finder is usually sufficient.
        cycles = []
        
        # Get all active allocations in this batch
        allocs = list(BedAllocation.objects.filter(
            is_active=True,
            allocation_run__batch_id=batch_id
        ).select_related('student', 'bed__room'))
        
        alloc_dict = {a.student.id: a for a in allocs}
        
        for a in allocs:
            try:
                # Get the students A wants to room with
                requested_ids = list(a.student.preference.roommate_requests.values_list('user__student_profile__id', flat=True))
                
                for b_id in requested_ids:
                    # Check if B has an allocation
                    if b_id in alloc_dict and b_id > a.student.id: # Avoid duplicates
                        b_alloc = alloc_dict[b_id]
                        try:
                            # Check if B wants to room with A
                            b_requested_ids = list(b_alloc.student.preference.roommate_requests.values_list('user__student_profile__id', flat=True))
                            if a.student.id in b_requested_ids:
                                # Found a mutual request. Check if their rooms are different
                                if a.bed.room_id != b_alloc.bed.room_id:
                                    cycles.append({
                                        'student_a': a.student.id,
                                        'student_b': b.student.id,
                                        'bed_a': a.bed.id,
                                        'bed_b': b_alloc.bed.id,
                                        'room_a': a.bed.room_id,
                                        'room_b': b_alloc.bed.room_id,
                                        'cycle_length': 2
                                    })
                        except Preference.DoesNotExist:
                            pass
            except Preference.DoesNotExist:
                pass
                
        return cycles

    @staticmethod
    @transaction.atomic
    def execute_swap(student_a_id, student_b_id):
        """
        Executes a direct 2-way swap between A and B if valid.
        """
        try:
            alloc_a = BedAllocation.objects.get(student_id=student_a_id, is_active=True)
            alloc_b = BedAllocation.objects.get(student_id=student_b_id, is_active=True)
        except BedAllocation.DoesNotExist:
            raise ValueError("One or both students do not have an active allocation.")
            
        if alloc_a.bed.room.floor.block.hostel.gender_type != alloc_b.bed.room.floor.block.hostel.gender_type:
            raise ValueError("Cannot swap across different gender hostels.")
            
        # Swap beds
        bed_a_temp = alloc_a.bed
        alloc_a.bed = alloc_b.bed
        alloc_b.bed = bed_a_temp
        
        alloc_a.save(update_fields=['bed'])
        alloc_b.save(update_fields=['bed'])
        
        return True
