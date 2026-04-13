from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class UserService:
    @staticmethod
    @transaction.atomic
    def create_user(username, password, email, role='CUSTOMER', phone_number=None):
        """
        Creates a new user with the specified role and securely hashes the password.
        Default role is CUSTOMER for public registrations.
        """
        user = User(
            username=username,
            email=email,
            role=role,
            phone_number=phone_number
        )
        user.set_password(password)
        user.save()
        return user
