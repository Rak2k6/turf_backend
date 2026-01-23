import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_backend.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.auth import get_user_model
from tenants.models import Tenant
from bookings.models import Court

User = get_user_model()

def verify():
    client = APIClient()
    
    print("\n--- Testing Auth ---")
    # Login
    response = client.post('/api/auth/login/', {'username': 'turfowner', 'password': 'ownerpass123'})
    if response.status_code == 200:
        print("Login Success")
        token = response.data['access']
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
    else:
        print("Login Failed", response.data)
        return

    print("\n--- Testing Tenant API ---")
    # Get My Tenant
    response = client.get('/api/my-tenant/')
    if response.status_code == 200:
        print(f"My Tenant: {response.data['name']} (Subdomain: {response.data['subdomain']})")
    else:
        print("Get My Tenant Failed", response.data)

    print("\n--- Testing Courts API ---")
    # List Courts
    response = client.get('/api/courts/')
    if response.status_code == 200:
        print(f"Courts Found: {len(response.data)}")
        if len(response.data) > 0:
            court_id = response.data[0]['id']
            print(f"Court ID: {court_id}")
    else:
        print("List Courts Failed", response.data)
        return

    print("\n--- Testing Availability API ---")
    response = client.get(f'/api/availability/?court_id={court_id}&date=2024-12-01')
    if response.status_code == 200:
        slots = response.data
        print(f"Slots generated: {len(slots)}")
        print(f"First slot: {slots[0]}")
    else:
        print("Availability Check Failed", response.data)

    print("\n--- Testing Booking API ---")
    # Create Booking
    booking_data = {
        'court': court_id,
        'start_time': '2024-12-01T10:00:00Z',
        'end_time': '2024-12-01T11:00:00Z'
    }
    response = client.post('/api/bookings/', booking_data)
    if response.status_code == 201:
        print("Booking Created Success", response.data['id'])
    else:
        print("Booking Creation Failed", response.data)

    # Verify Availability Updated
    print("\n--- Verifying Slot Taken ---")
    response = client.get(f'/api/availability/?court_id={court_id}&date=2024-12-01')
    taken_slot = next((s for s in response.data if s['start_time'] == '10:00'), None)
    if taken_slot:
        print(f"Slot 10:00 is available? {taken_slot['is_available']}")
    
if __name__ == '__main__':
    verify()
