from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import RegisterView, MyTokenObtainPairView, UserProfileView
from tenants.views import TenantViewSet, MeTenantView
from bookings.views import CourtViewSet, BookingViewSet, SlotAvailabilityView
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'tenants', TenantViewSet)
router.register(r'courts', CourtViewSet)
router.register(r'bookings', BookingViewSet, basename='booking')
# router.register(r'me/tenant', MeTenantView, basename='me-tenant') 
# ViewSet generic view needs specific setup for 'list' usually, 
# 'MeTenantView' inherits GenericViewSet and has 'list', so better register explicitly or use router properly.
# MeTenantView handles 'list' for GET /me/tenant/ (but router expects id for detail).
# Let's map MeTenantView manually to avoid router issues with singleton resource.

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', UserProfileView.as_view(), name='auth_profile'),

    # Application
    path('api/', include(router.urls)),
    path('api/my-tenant/', MeTenantView.as_view({'get': 'list'}), name='my_tenant'),
    path('api/availability/', SlotAvailabilityView.as_view(), name='slot_availability'),
]
