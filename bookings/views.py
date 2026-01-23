from rest_framework import viewsets, permissions, filters, views
from rest_framework.response import Response
from .models import Court, Booking
from .serializers import CourtSerializer, BookingSerializer
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q

class IsTurfOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.tenant.owner == request.user

class CourtViewSet(viewsets.ModelViewSet):
    serializer_class = CourtSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Court.objects.all()

    def get_queryset(self):
        queryset = Court.objects.all()
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        # If user is TurfAdmin, arguably they should only manage their own courts
        # But for public listing, we might want to see all.
        return queryset

    def perform_create(self, serializer):
        # Allow creating court only for owned tenant
        # Assuming user has one tenant
        if not hasattr(self.request.user, 'owned_tenant'):
             raise permissions.PermissionDenied("You do not have a registered turf.")
        serializer.save(tenant=self.request.user.owned_tenant)

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return Booking.objects.all()
        elif user.role == 'TURF_ADMIN':
            # Bookings for my turf's courts
            return Booking.objects.filter(court__tenant__owner=user)
        else:
            # Customer/Staff sees their own bookings (or staff sees turf bookings? Design says Staff manages operations)
            if user.role == 'STAFF':
                # Assuming staff is linked to a tenant (not implemented yet).
                # For now, let Staff see everything or implement association later.
                # Fallback: Staff sees nothing or their own bookings.
                return Booking.objects.filter(customer=user)
            return Booking.objects.filter(customer=user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class SlotAvailabilityView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        court_id = request.query_params.get('court_id')
        date_str = request.query_params.get('date') # YYYY-MM-DD

        if not court_id or not date_str:
            return Response({"error": "court_id and date are required"}, status=400)

        try:
            court = Court.objects.get(id=court_id)
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Court.DoesNotExist:
             return Response({"error": "Court not found"}, status=404)
        except ValueError:
             return Response({"error": "Invalid date format"}, status=400)

        # Generate slots based on opening/closing time
        opening = datetime.combine(target_date, court.opening_time)
        closing = datetime.combine(target_date, court.closing_time)
        slot_duration = timedelta(minutes=court.slot_duration_mins)

        slots = []
        current_time = opening
        while current_time + slot_duration <= closing:
            end_time = current_time + slot_duration
            
            # Check availability
            # Naive: query DB for overlaps for EACH slot (N queries). Better: Fetch all bookings for day and check in memory.
            # Optimization: 1 query
            existing_bookings = Booking.objects.filter(
                court=court,
                status__in=['CONFIRMED', 'PENDING'],
                start_time__lt=end_time,
                end_time__gt=current_time
            )

            is_available = not existing_bookings.exists()
            
            slots.append({
                "start_time": current_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "is_available": is_available
            })
            
            current_time = end_time

        return Response(slots)
