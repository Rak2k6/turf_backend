from rest_framework import serializers
from .models import Court, Booking
from django.utils import timezone
from datetime import timedelta

class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = '__all__'
        read_only_fields = ('tenant',)

class BookingSerializer(serializers.ModelSerializer):
    court_name = serializers.ReadOnlyField(source='court.name')
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('total_price', 'status', 'payment_status', 'created_at')

    def validate(self, data):
        start_time = data['start_time']
        end_time = data['end_time']
        court = data['court']

        # Ensure start < end
        if start_time >= end_time:
            raise serializers.ValidationError("End time must be after start time.")
        
        # Check overlaps
        # (StartA < EndB) and (EndA > StartB)
        overlaps = Booking.objects.filter(
            court=court,
            status__in=['CONFIRMED', 'PENDING'],
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        if self.instance:
            overlaps = overlaps.exclude(id=self.instance.id)

        if overlaps.exists():
            raise serializers.ValidationError("This slot is already booked.")

        return data

    def create(self, validated_data):
        # Calculate price (simple logic: duration * price_per_hour)
        court = validated_data['court']
        start_time = validated_data['start_time']
        end_time = validated_data['end_time']
        
        duration = end_time - start_time
        hours = duration.total_seconds() / 3600
        
        price = float(court.base_price_per_hour) * hours
        validated_data['total_price'] = round(price, 2)
        
        return super().create(validated_data)
