from rest_framework import permissions

class IsTenantOwner(permissions.BasePermission):
    """
    Check if the user is the owner of the tenant that the object belongs to.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['TURF_ADMIN', 'SUPER_ADMIN']

    def has_object_permission(self, request, view, obj):
        # Super admin can do anything
        if request.user.role == 'SUPER_ADMIN':
            return True
        
        # Check ownership based on the object type
        if hasattr(obj, 'owner'): # For Tenant itself
            return obj.owner == request.user
        
        if hasattr(obj, 'tenant'): # For Court or Slot
            return obj.tenant.owner == request.user
            
        if hasattr(obj, 'court'): # For Booking
            return obj.court.tenant.owner == request.user
            
        return False

class IsBookingOwner(permissions.BasePermission):
    """
    Allow users to see and manage their own bookings.
    """
    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user or request.user.role in ['TURF_ADMIN', 'SUPER_ADMIN']

class IsStaffOrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['STAFF', 'TURF_ADMIN', 'SUPER_ADMIN']
