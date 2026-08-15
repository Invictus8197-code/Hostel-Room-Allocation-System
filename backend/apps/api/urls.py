from django.urls import path, include
from rest_framework.routers import DefaultRouter
from backend.apps.api.views import (
    CustomTokenObtainPairView, CustomTokenRefreshView, LogoutView,
    DashboardSummaryView, ApplicationBatchViewSet, AllocationRunViewSet,
    AnalyticsHostelsView, SimulationRunView
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
    
    # Analytics
    path('analytics/hostels/', AnalyticsHostelsView.as_view(), name='analytics_hostels'),
    
    # Simulation
    path('simulations/run/', SimulationRunView.as_view(), name='simulations_run'),
    
    # Router (Allocations)
    path('', include(router.urls)),
]
