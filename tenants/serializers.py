from rest_framework import serializers
from .models import Tenant

class TenantSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Tenant
        fields = '__all__'
        read_only_fields = ('owner', 'created_at')

class TenantBrandingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ('logo', 'primary_color', 'secondary_color', 'description')
