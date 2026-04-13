from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .services import UserService

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'phone_number')
        read_only_fields = ('id', 'role') # Role should not be set by user during basic registration

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='CUSTOMER')

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'role', 'phone_number')
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate_password(self, value):
        validate_password(value, user=User(**self.initial_data))
        return value

    def validate_role(self, value):
        """
        Only Super Admins or Turf Admins can create non-CUSTOMER roles.
        """
        request = self.context.get('request')
        
        # If public registration (not authenticated)
        if not request or not request.user or not request.user.is_authenticated:
            if value != 'CUSTOMER':
                raise serializers.ValidationError("Only admins can create non-customer accounts.")
            return value

        # If authenticated, check if the user is an admin
        if value in ['TURF_ADMIN', 'STAFF', 'SUPER_ADMIN']:
            if request.user.role not in ['SUPER_ADMIN', 'TURF_ADMIN']:
                raise serializers.ValidationError(f"You do not have permission to create a user with role: {value}")
        
        return value

    def create(self, validated_data):
        return UserService.create_user(**validated_data)
