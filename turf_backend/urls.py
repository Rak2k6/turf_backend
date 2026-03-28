from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from users.views import RegisterView, MyTokenObtainPairView, UserProfileView
from tenants.views import TenantViewSet, MeTenantView
from bookings.views import CourtViewSet, BookingViewSet, SlotAvailabilityView, SlotViewSet, DashboardAnalyticsView
from rest_framework_simplejwt.views import TokenRefreshView

router = routers.DefaultRouter()
router.register(r'tenants', TenantViewSet)

# Nested Router for Tenants
tenants_router = routers.NestedSimpleRouter(router, r'tenants', lookup='tenant')
tenants_router.register(r'courts', CourtViewSet, basename='tenant-courts')
tenants_router.register(r'slots', SlotViewSet, basename='tenant-slots')
tenants_router.register(r'bookings', BookingViewSet, basename='tenant-bookings')

# Root routers for general access (optional, but keep for now)
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', UserProfileView.as_view(), name='auth_profile'),

    # Application
    path('api/', include(router.urls)),
    path('api/', include(tenants_router.urls)),
    path('api/my-tenant/', MeTenantView.as_view({'get': 'list'}), name='my_tenant'),
    path('api/availability/', SlotAvailabilityView.as_view(), name='slot_availability'),
    path('api/dashboard/<str:metric>/', DashboardAnalyticsView.as_view(), name='dashboard_analytics'),
]
