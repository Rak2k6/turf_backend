from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthSecurityTests(APITestCase):
    def test_register_hashes_password_and_hides_it_in_response(self):
        payload = {
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'SecurePass123!',
            'role': 'CUSTOMER',
            'phone_number': '1234567890',
        }

        response = self.client.post('/api/auth/register/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        self.assertEqual(response.data['role'], 'CUSTOMER')

        user = User.objects.get(username='alice')
        self.assertNotEqual(user.password, payload['password'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertEqual(user.role, 'CUSTOMER')

    def test_register_as_turf_admin_denied_to_public(self):
        payload = {
            'username': 'malicious',
            'email': 'malicious@example.com',
            'password': 'SecurePass123!',
            'role': 'TURF_ADMIN',
        }

        # Public (unauthenticated) attempt to register as an admin
        response = self.client.post('/api/auth/register/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', response.data)
        self.assertEqual(response.data['role'][0], "Only admins can create non-customer accounts.")

    def test_register_defaults_to_customer(self):
        payload = {
            'username': 'regular_user',
            'email': 'regular@example.com',
            'password': 'SecurePass123!',
        }

        response = self.client.post('/api/auth/register/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='regular_user')
        self.assertEqual(user.role, 'CUSTOMER')

    def test_admin_can_create_turf_admin(self):
        admin = User.objects.create_user(username='super', password='adminpass123', role='SUPER_ADMIN')
        self.client.force_authenticate(user=admin)
        
        payload = {
            'username': 'new_turf_admin',
            'email': 'new_admin@example.com',
            'password': 'SecurePass123!',
            'role': 'TURF_ADMIN',
        }

        response = self.client.post('/api/auth/register/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='new_turf_admin')
        self.assertEqual(user.role, 'TURF_ADMIN')


    def test_register_rejects_short_passwords(self):
        payload = {
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'short',
        }

        response = self.client.post('/api/auth/register/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_authenticates_hashed_password_and_returns_jwt_tokens(self):
        user = User(username='charlie', email='charlie@example.com')
        user.set_password('SecurePass123!')
        user.save()

        response = self.client.post(
            '/api/auth/login/',
            {'username': 'charlie', 'password': 'SecurePass123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
