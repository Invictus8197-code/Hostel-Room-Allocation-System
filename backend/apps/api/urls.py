from django.urls import path, include
from rest_framework.routers import DefaultRouter
from backend.apps.api.views import (
    CustomTokenObtainPairView, CustomTokenRefreshView, LogoutView,
    DashboardSummaryView, DashboardFloorplanView, ApplicationBatchViewSet, AllocationRunViewSet,
    AnalyticsHostelsView, SimulationRunView, WardenAssignmentView,
    SwapCycleView, ExecuteSwapView
)

router = DefaultRouter()
router.register(r'allocations/batches', ApplicationBatchViewSet, basename='batch')
router.register(r'allocations/runs', AllocationRunViewSet, basename='run')

urlpatterns = [
    # Auth
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('dashboard/floorplan/', DashboardFloorplanView.as_view(), name='dashboard_floorplan'),
    
    # Analytics
    path('analytics/hostels/', AnalyticsHostelsView.as_view(), name='analytics_hostels'),
    
    # Simulation
    path('simulations/run/', SimulationRunView.as_view(), name='simulations_run'),
    
    # Superadmin Operations
    path('superadmin/wardens/<int:warden_user_id>/assign-hostels/', WardenAssignmentView.as_view(), name='warden_assign_hostels'),
    
    # Swap System
    path('allocations/batches/<int:batch_id>/swaps/', SwapCycleView.as_view(), name='swap_cycles'),
    path('allocations/swaps/execute/', ExecuteSwapView.as_view(), name='execute_swap'),

    # Router (Allocations)
    path('', include(router.urls)),
]
