from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action

from backend.apps.api.permissions import IsAdminOrWarden, IsAdminUserRole
from backend.apps.api.serializers import ApplicationBatchSerializer, AllocationRunSerializer, AllocationRunDetailSerializer
from backend.apps.applications.models import ApplicationBatch, StudentApplication
from backend.apps.allocations.models import AllocationRun
from backend.apps.hostels.models import Bed
from backend.apps.allocations.services.allocation_service import (
    AllocationService, AllocationCommitService, 
    InvalidBatchError, OptimizationError, InvalidRunStateError, ConcurrencyConflictError
)
from backend.apps.analytics.services import AnalyticsService
from backend.apps.simulations.services.simulation_service import SimulationService
from datetime import datetime

# --- Auth ---
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            del response.data['refresh']
        return response

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            request.data['refresh'] = refresh_token
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200 and 'refresh' in response.data:
            response.set_cookie(
                key='refresh_token',
                value=response.data['refresh'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            del response.data['refresh']
        return response

class LogoutView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request):
        response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token')
        return response

# --- Dashboard ---
class DashboardSummaryView(APIView):
    permission_classes = [IsAdminOrWarden]

    def get(self, request):
        # We need a start_date and end_date for analytics. 
        # For a general dashboard, we can use the latest batch or current date.
        latest_batch = ApplicationBatch.objects.order_by('-start_date').first()
        
        start_date = latest_batch.start_date if latest_batch else datetime.now().date()
        end_date = latest_batch.end_date if latest_batch else datetime.now().date()
        
        hostel_utils = AnalyticsService.get_hostel_utilization(start_date, end_date)
        
        total_beds = sum(h['total_beds'] for h in hostel_utils)
        occupied_beds = sum(h['occupied_beds'] for h in hostel_utils)
        utilization = (occupied_beds / total_beds) if total_beds > 0 else 0.0
        
        total_students = StudentApplication.objects.count()
        latest_run = AllocationRun.objects.order_by('-run_date').first()
        
        # Calculate underutilized rooms globally using get_room_utilization
        room_utils = AnalyticsService.get_room_utilization(start_date, end_date)
        underutilized_rooms = sum(1 for r in room_utils if r['underutilized'])
        
        # We don't have a direct global "allocated students" count independent of a batch easily without BedAllocation queries.
        # Let's count active bed allocations as global occupied beds, which is equal to allocated students currently active.
        
        return Response({
            "total_students": total_students,
            "allocated_students": occupied_beds, 
            "unallocated_students": total_students - occupied_beds,
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "vacant_beds": total_beds - occupied_beds,
            "utilization": utilization,
            "underutilized_rooms": underutilized_rooms,
            "latest_allocation_run": AllocationRunSerializer(latest_run).data if latest_run else None,
            "active_batch": ApplicationBatchSerializer(latest_batch).data if latest_batch else None
        })

# --- Allocations ---
class ApplicationBatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApplicationBatch.objects.all().order_by('-start_date')
    serializer_class = ApplicationBatchSerializer
    permission_classes = [IsAdminOrWarden]

class AllocationRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AllocationRun.objects.all().order_by('-run_date')
    permission_classes = [IsAdminOrWarden]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AllocationRunDetailSerializer
        return AllocationRunSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUserRole])
    def draft(self, request):
        batch_id = request.data.get('batch_id')
        if not batch_id:
            return Response({"error": "batch_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            run = AllocationService.create_draft_run(batch_id)
            return Response(AllocationRunDetailSerializer(run).data, status=status.HTTP_201_CREATED)
        except InvalidBatchError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except OptimizationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserRole])
    def approve(self, request, pk=None):
        try:
            run = AllocationService.approve_run(pk)
            return Response(AllocationRunDetailSerializer(run).data)
        except InvalidRunStateError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserRole])
    def commit(self, request, pk=None):
        try:
            run = AllocationCommitService.commit_run(pk)
            return Response(AllocationRunDetailSerializer(run).data)
        except (InvalidRunStateError, ConcurrencyConflictError) as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

# --- Analytics ---
class AnalyticsHostelsView(APIView):
    permission_classes = [IsAdminOrWarden]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response({"error": "start_date and end_date are required query params."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Parse dates
            s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            e_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
        result = AnalyticsService.get_hostel_utilization(s_date, e_date)
        return Response(result)

# --- Simulation ---
class SimulationRunView(APIView):
    permission_classes = [IsAdminOrWarden]

    def post(self, request):
        batch_id = request.data.get('batch_id')
        scenario = request.data.get('scenario', {})
        
        if not batch_id:
            return Response({"error": "batch_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            result = SimulationService.run_simulation(batch_id, scenario)
            return Response(result)
        except ValueError as e:
            # Could be batch not found or invalid student IDs
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
