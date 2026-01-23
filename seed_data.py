
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'turf_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from tenants.models import Tenant
from bookings.models import Court

User = get_user_model()

def seed():
    # 1. Create Superuser
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'password123')
        admin.role = 'SUPER_ADMIN'
        admin.save()
        print("Superuser 'admin' created.")

    # 2. Create Turf Admin
    if not User.objects.filter(username='turfowner').exists():
        owner = User.objects.create_user('turfowner', 'owner@example.com', 'ownerpass123')
        owner.role = 'TURF_ADMIN'
        owner.save()
        print("Turf Admin 'turfowner' created.")
    else:
        owner = User.objects.get(username='turfowner')

    # 3. Create Tenant
    if not Tenant.objects.filter(subdomain='bestturf').exists():
        tenant = Tenant.objects.create(
            name="Best Turf",
            subdomain="bestturf",
            owner=owner,
            primary_color="#00FF00"
        )
        print(f"Tenant '{tenant.name}' created.")
    else:
        tenant = Tenant.objects.get(subdomain='bestturf')

    # 4. Create Court
    if not tenant.courts.exists():
        court = Court.objects.create(
            tenant=tenant,
            name="Court A",
            sport_type="FOOTBALL",
            base_price_per_hour=1000.00
        )
        print(f"Court '{court.name}' created.")

if __name__ == '__main__':
    seed()
