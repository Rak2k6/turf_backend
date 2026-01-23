from rest_framework import viewsets, permissions, exceptions
from rest_framework.response import Response
from .models import Tenant
from .serializers import TenantSerializer, TenantBrandingSerializer

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'SUPER_ADMIN'

class IsTurfOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsSuperAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsTurfOwner()] # Or SuperAdmin
        return [permissions.AllowAny()] # Allow listing/viewing by public (for discovery if needed) or restrict

    def perform_create(self, serializer):
        # In a real scenario, we might assign owner from request data or assume current user is creating it for themselves if allowed
        # But here SuperAdmin creates tenants and assigns owners.
        # For MVP, let's assume the request passes an owner ID or we assign it.
        # Let's just save for now.
        serializer.save()

class MeTenantView(viewsets.GenericViewSet):
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        if not hasattr(request.user, 'owned_tenant'):
            raise exceptions.NotFound("No tenant found for this user")
        serializer = self.get_serializer(request.user.owned_tenant)
        return Response(serializer.data)
