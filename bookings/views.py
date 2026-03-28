from rest_framework import viewsets, permissions, filters, views, status as http_status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from .models import Court, Booking, Slot
from .serializers import CourtSerializer, BookingSerializer, SlotSerializer
from .permissions import IsTenantOwner, IsStaffOrOwner, IsBookingOwner
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Sum, Count
from django_filters.rest_framework import DjangoFilterBackend

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class CourtViewSet(viewsets.ModelViewSet):
    serializer_class = CourtSerializer
    queryset = Court.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tenant', 'sport_type', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'base_price_per_hour']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTenantOwner()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        # Handle Nested Router Case: /api/tenants/{tenant_pk}/courts/
        tenant_pk = self.kwargs.get('tenant_lookup') # from NestedSimpleRouter lookup='tenant'
        if tenant_pk:
            return Court.objects.filter(tenant_id=tenant_pk)
            
        queryset = Court.objects.all()
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset

    def perform_create(self, serializer):
        tenant_pk = self.kwargs.get('tenant_lookup')
        if tenant_pk:
            # Verify ownership if nested
            if self.request.user.role == 'TURF_ADMIN' and str(self.request.user.owned_tenant.id) != tenant_pk:
                raise permissions.PermissionDenied("You do not own this tenant.")
            serializer.save(tenant_id=tenant_pk)
        else:
            if not hasattr(self.request.user, 'owned_tenant'):
                 raise permissions.PermissionDenied("You do not have a registered turf.")
            serializer.save(tenant=self.request.user.owned_tenant)

class SlotViewSet(viewsets.ModelViewSet):
    serializer_class = SlotSerializer
    queryset = Slot.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['court', 'is_active']
    ordering_fields = ['start_time']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTenantOwner()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        tenant_pk = self.kwargs.get('tenant_lookup')
        if tenant_pk:
            return Slot.objects.filter(court__tenant_id=tenant_pk)
            
        queryset = Slot.objects.all()
        court_id = self.request.query_params.get('court')
        if court_id:
            queryset = queryset.filter(court_id=court_id)
        return queryset

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['court', 'status', 'payment_status', 'date']
    ordering_fields = ['created_at', 'date', 'start_time']

    def get_permissions(self):
        if self.action in ['confirm', 'cancel']:
            return [IsTenantOwner()]
        if self.action in ['retrieve', 'my_bookings']:
            return [IsBookingOwner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        tenant_pk = self.kwargs.get('tenant_lookup')
        
        base_queryset = Booking.objects.all()
        if tenant_pk:
            base_queryset = base_queryset.filter(court__tenant_id=tenant_pk)

        if user.role == 'SUPER_ADMIN':
            return base_queryset.order_by('-created_at')
        elif user.role == 'TURF_ADMIN':
            # Tenant owners only see their own tenant's bookings
            return base_queryset.filter(court__tenant__owner=user).order_by('-created_at')
        else:
            # Customers see their own bookings (optionally filtered by tenant if nested)
            return base_queryset.filter(customer=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    @action(detail=False, methods=['get'], url_path='my-bookings')
    def my_bookings(self, request):
        """
        Custom endpoint for users to see their own bookings.
        """
        queryset = self.get_queryset().filter(customer=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        if booking.status == 'CANCELLED':
            return Response({"error": "Cannot confirm a cancelled booking"}, status=400)
        booking.status = 'CONFIRMED'
        booking.save()
        return Response({'status': 'booking confirmed'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'CANCELLED'
        booking.save()
        return Response({'status': 'booking cancelled'})


class SlotAvailabilityView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        court_id = request.query_params.get('court')
        date_str = request.query_params.get('date') # YYYY-MM-DD

        if not court_id or not date_str:
            return Response({"error": "court and date are required"}, status=400)

        try:
            court = Court.objects.get(id=court_id)
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Court.DoesNotExist:
             return Response({"error": "Court not found"}, status=404)
        except ValueError:
             return Response({"error": "Invalid date format"}, status=400)

        # Fetch defined slots for this court
        slots = Slot.objects.filter(court=court, is_active=True).order_by('start_time')
        
        # Fetch bookings for this court and date (exclude CANCELLED)
        booked_slot_ids = Booking.objects.filter(
            court=court,
            date=target_date,
        ).exclude(status='CANCELLED').values_list('slot_id', flat=True)

        available_slots = []
        for slot in slots:
            available_slots.append({
                "id": slot.id,
                "start_time": slot.start_time.strftime("%H:%M"),
                "end_time": slot.end_time.strftime("%H:%M"),
                "price": slot.price,
                "is_available": slot.id not in booked_slot_ids
            })

        return Response(available_slots)

class DashboardAnalyticsView(views.APIView):
    permission_classes = [IsTenantOwner]

    def get_tenant(self, request):
        if hasattr(request.user, 'owned_tenant'):
            return request.user.owned_tenant
        return None

    def get(self, request, metric=None):
        tenant = self.get_tenant(request)
        if not tenant:
            return Response({"error": "Tenant not found"}, status=404)

        today = timezone.now().date()
        # Strictly exclude CANCELLED from all counts/sums
        base_queryset = Booking.objects.filter(court__tenant=tenant).exclude(status='CANCELLED')

        if metric == 'today-bookings':
            count = base_queryset.filter(date=today).count()
            return Response({"count": count})

        elif metric == 'today-revenue':
            # Only CONFIRMED counts as revenue in production
            revenue = base_queryset.filter(date=today, status='CONFIRMED').aggregate(total=Sum('total_price'))['total'] or 0
            return Response({"revenue": float(revenue)})

        elif metric == 'total-bookings':
            count = base_queryset.count()
            return Response({"count": count})

        elif metric == 'court-stats':
            stats = base_queryset.values('court__name').annotate(count=Count('id')).order_by('-count')
            return Response(list(stats))

        return Response({"error": "Invalid metric"}, status=400)
