import os
import django
import json
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_backend.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from bookings.models import Court, Slot, Booking

User = get_user_model()

def verify():
    client = APIClient()
    
    # 1. Login as Turf Admin
    print("\n--- 1. Login ---")
    response = client.post('/api/auth/login/', {'username': 'turfowner', 'password': 'ownerpass123'})
    if response.status_code == 200:
        token = response.data['access']
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        print("Login Success")
    else:
        print("Login Failed", response.data)
        return

    # 2. Setup a Court and some Slots
    court = Court.objects.first()
    if not court:
        print("No Court found! Seeding initial data might be needed.")
        return
    print(f"\n--- 2. Creating Slots for Court ID: {court.id} ({court.name}) ---")
    
    # Clear existing slots to be sure
    Slot.objects.filter(court=court).delete()
    
    slot1_data = {
        "court": court.id,
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "price": "1200.00",
        "is_active": True
    }
    response = client.post('/api/slots/', slot1_data)
    if response.status_code == 201:
        slot1_id = response.data['id']
        print(f"Slot 1 Created: {slot1_id}")
    else:
        print("Slot 1 Creation Failed", response.data)
        return

    slot2_data = {
        "court": court.id,
        "start_time": "11:00:00",
        "end_time": "12:00:00",
        "price": "1200.00",
        "is_active": True
    }
    response = client.post('/api/slots/', slot2_data)
    if response.status_code == 201:
        slot2_id = response.data['id']
        print(f"Slot 2 Created: {slot2_id}")

    # Verify slots exist in DB for this court
    all_slots = Slot.objects.filter(court=court)
    print(f"Total Slots in DB for Court {court.id}: {all_slots.count()}")
    for s in all_slots:
        print(f"  Slot {s.id}: {s.start_time} - {s.end_time} (Active: {s.is_active})")

    # 3. Check Availability
    print("\n--- 3. Checking Availability ---")
    test_date = "2024-12-05"
    response = client.get(f'/api/availability/?court={court.id}&date={test_date}')
    if response.status_code == 200:
        print(f"Slots Found in API: {len(response.data)}")
        for s in response.data:
            print(f"Slot {s['id']}: {s['start_time']} - {s['is_available']}")
    else:
        print("Availability failed", response.data)

    # 4. Create a Booking for Slot 1
    print("\n--- 4. Creating Booking for Slot 1 ---")
    booking_data = {
        "court": court.id,
        "slot": slot1_id,
        "date": test_date
    }
    response = client.post('/api/bookings/', booking_data)
    if response.status_code == 201:
        booking_id = response.data['id']
        print(f"Booking Created: {booking_id}")
    else:
        print("Booking Failed", response.data)

    # 5. Verify Availability Updated
    print("\n--- 5. Verifying Slot 1 is now taken ---")
    response = client.get(f'/api/availability/?court={court.id}&date={test_date}')
    s1 = next((s for s in response.data if s['id'] == slot1_id), None)
    if s1:
        print(f"Slot 1 Available: {s1['is_available']}")
    
    # 6. Test Dashboard
    print("\n--- 6. Testing Dashboard Analytics ---")
    # Mark booking as confirmed for revenue test
    b = Booking.objects.get(id=booking_id)
    b.status = 'CONFIRMED'
    b.date = datetime.now().date() # Set to today for dashboard test
    b.save()

    metrics = ['today-bookings', 'today-revenue', 'total-bookings', 'court-stats']
    for m in metrics:
        response = client.get(f'/api/dashboard/{m}/')
        if response.status_code == 200:
            print(f"Dashboard {m}: {response.data}")
        else:
            print(f"Dashboard {m} Failed", response.data)

if __name__ == '__main__':
    verify()
