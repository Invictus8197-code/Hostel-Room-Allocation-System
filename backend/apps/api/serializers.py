from rest_framework import serializers
from backend.apps.applications.models import ApplicationBatch, StudentApplication
from backend.apps.allocations.models import AllocationRun, BedAllocation
from backend.apps.accounts.models import StudentProfile

class ApplicationBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationBatch
        fields = '__all__'

class AllocationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllocationRun
        fields = '__all__'

class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'registration_number', 'department', 'course_year', 'gender', 'username', 'full_name']

class BedAllocationSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer()
    bed_number = serializers.CharField(source='bed.bed_number', read_only=True)
    room_number = serializers.CharField(source='bed.room.room_number', read_only=True)
    hostel_name = serializers.CharField(source='bed.room.floor.block.hostel.name', read_only=True)
    
    class Meta:
        model = BedAllocation
        fields = ['id', 'student', 'bed', 'bed_number', 'room_number', 'hostel_name', 'start_date', 'end_date', 'is_active']

class AllocationRunDetailSerializer(serializers.ModelSerializer):
    allocations = serializers.SerializerMethodField()
    
    class Meta:
        model = AllocationRun
        fields = ['id', 'status', 'run_date', 'fairness_score', 'summary_data', 'allocations']

    def get_allocations(self, obj):
        # We only want to fetch bed allocations for this run
        allocs = obj.bed_allocations.select_related('student__user', 'bed__room__floor__block__hostel')
        return BedAllocationSerializer(allocs, many=True).data
