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
    
    # login as customer
    print("\n--- 1. Login as Customer ---")
    customer_username = 'customer1'
    # Create customer if doesn't exist (simulating registration if needed, but let's assume seeded)
    try:
        user = User.objects.get(username=customer_username)
    except User.DoesNotExist:
        user = User.objects.create_user(username=customer_username, password='password123', role='CUSTOMER')
    
    response = client.post('/api/auth/login/', {'username': customer_username, 'password': 'password123'})
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
    print("Customer Login Success")

    court = Court.objects.first()
    slot = Slot.objects.filter(court=court).first()
    # Use a far future date to avoid conflicts with previous runs
    test_date = datetime.now().date() + timedelta(days=100)
    
    # 2. Test Double Booking (Using Nested URL)
    print(f"\n--- 2. Testing Double Booking (Nested) for {test_date} ---")
    Booking.objects.filter(court=court, slot=slot, date=test_date).delete()
    
    # POST to /api/tenants/{id}/bookings/
    nested_url = f'/api/tenants/{court.tenant.id}/bookings/'
    data = {"court": court.id, "slot": slot.id, "date": test_date}
    
    # First booking
    res1 = client.post(nested_url, data)
    print(f"First Booking Status (Nested): {res1.status_code}") 
    if res1.status_code != 201:
        print("First Booking Failed!", res1.data)
        return
    
    # Second booking
    print("Attempting second booking for same slot/date via Nested URL...")
    res2 = client.post(nested_url, data)
    print(f"Second Booking Attempt Status: {res2.status_code}")
    if res2.status_code == 400:
        print("Success: Double booking prevented with 400 error")
    else:
        print("Failure: Double booking not prevented or wrong error code", res2.data)

    # 3. Test My Bookings
    print("\n--- 3. Testing My Bookings ---")
    res3 = client.get('/api/bookings/my-bookings/')
    if res3.status_code == 200:
        print(f"My Bookings Found: {len(res3.data['results'])}")
    else:
        print("My Bookings Failed", res3.data)

    # 4. Test Isolation
    print("\n--- 4. Testing Tenant isolation (Trying to confirm as user) ---")
    booking_id = res1.data['id']
    res4 = client.post(f'/api/bookings/{booking_id}/confirm/')
    print(f"Confirm Attempt (User): {res4.status_code}") # Should be 403
    if res4.status_code == 403:
        print("Success: Forbidden for user")

    # 5. Login as Owner to confirm
    print("\n--- 5. Confirming as Owner ---")
    client.credentials() # Clear credentials
    response = client.post('/api/auth/login/', {'username': 'turfowner', 'password': 'ownerpass123'})
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
    
    res5 = client.post(f'/api/bookings/{booking_id}/confirm/')
    print(f"Confirm Attempt (Owner): {res5.status_code}") # Should be 200

    # 6. Test Dashboard (Cancelled Filter)
    print("\n--- 6. Testing Dashboard Analytics (Cancelled exclusion) ---")
    # Cancel the booking
    client.post(f'/api/bookings/{booking_id}/cancel/')
    print("Booking Cancelled")
    
    # Check dashboard today-bookings
    res6 = client.get('/api/dashboard/total-bookings/')
    print(f"Total Bookings in Dashboard: {res6.data['count']}")
    
if __name__ == '__main__':
    verify()
