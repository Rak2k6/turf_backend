from rest_framework import serializers
from .models import Court, Booking, Slot
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

class CourtSerializer(serializers.ModelSerializer):
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    
    class Meta:
        model = Court
        fields = '__all__'
        read_only_fields = ('tenant', 'is_active')

class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    court_name = serializers.ReadOnlyField(source='court.name')
    slot_details = SlotSerializer(source='slot', read_only=True)
    customer_username = serializers.ReadOnlyField(source='customer.username')
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('total_price', 'status', 'payment_status', 'created_at', 'start_time', 'end_time')

    def validate(self, data):
        # If slot is provided, use its times
        slot = data.get('slot')
        date = data.get('date')
        court = data.get('court')

        if slot:
            if slot.court != court:
                raise serializers.ValidationError({"court": "Slot does not belong to the selected court."})
            
            # Check overlap for this slot on this date (Exclude CANCELLED)
            overlaps = Booking.objects.filter(
                court=court,
                date=date,
                slot=slot,
            ).exclude(status='CANCELLED')
            
            if self.instance:
                overlaps = overlaps.exclude(id=self.instance.id)

            if overlaps.exists():
                raise serializers.ValidationError({"slot": "This slot is already booked for the selected date."})

        return data

    def create(self, validated_data):
        slot = validated_data.get('slot')
        date = validated_data.get('date')
        court = validated_data.get('court')

        if slot:
            # Set start/end times based on slot and date
            from datetime import datetime
            from django.utils import timezone
            
            start_dt = datetime.combine(date, slot.start_time)
            end_dt = datetime.combine(date, slot.end_time)
            
            # Make timezone aware if settings.USE_TZ is True
            if settings.USE_TZ:
                start_dt = timezone.make_aware(start_dt)
                end_dt = timezone.make_aware(end_dt)
                
            validated_data['start_time'] = start_dt
            validated_data['end_time'] = end_dt
            validated_data['total_price'] = slot.price
        
        # Explicitly use model manager to ensure read_only fields in Serializer 
        # that are manually added to validated_data are preserved.
        return Booking.objects.create(**validated_data)
