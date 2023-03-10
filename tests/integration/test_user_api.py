from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework.test import APITestCase

from tests.factories import UserFactory
from tests.utils import JWTMixin
from work_tracker.apps.users.models import User


class UserAPITestCase(APITestCase, JWTMixin):

    def test_user_auth_token_functionality(self):
        password = 'MyPrecious001!'
        user = UserFactory(password=make_password(password))
        url = reverse('api:auth-token')
        data = {
            'email': user.email,
            'password': password
        }
        # Assert successful obtaining of Auth token
        resp = self.client.post(url, data)
        assert resp.status_code == 200
        assert resp.data['refresh']
        assert resp.data['access']
        access_token = resp.data['access']
        refresh_token = resp.data['refresh']

        # Assert successful verification of Auth token
        url = reverse('api:auth-token-verify')
        data = {'token': access_token}
        resp = self.client.post(url, data)
        assert resp.status_code == 200

        # Assert successful refresh of Auth token
        url = reverse('api:auth-token-refresh')
        data = {"refresh": refresh_token}
        resp = self.client.post(url, data)
        assert resp.status_code == 200
        assert resp.data['access']
        access_token = resp.data['access']

        # Assert successful verification of refreshed Auth token
        url = reverse('api:auth-token-verify')
        data = {'token': access_token}
        resp = self.client.post(url, data)
        assert resp.status_code == 200

    def test_user_register(self):
        registration_data = {
            'email': 'merry@test.com',
            'password': 'MiniRohirrim1!',
            'first_name': 'Meriadoc',
            'last_name': 'Brandybuck',
            'rate': Decimal(15),
        }
        url = reverse('api:user-register')
        resp = self.client.post(url, registration_data)
        assert resp.status_code == 201
        assert User.objects.filter(email=registration_data['email']).exists()

        user = User.objects.get(email=registration_data['email'])
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active

        token = resp.data['token']
        url = reverse('api:auth-token-verify')
        data = {'token': token}
        resp = self.client.post(url, data)
        assert resp.status_code == 200

    def test_user_register_validation(self):
        user = UserFactory()
        registration_data = {
            'email': user.email,
            'password': 'MiniRohirrim1!',
            'first_name': 'Meriadoc',
            'last_name': 'Brandybuck',
            'rate': Decimal(15),
        }
        url = reverse('api:user-register')
        resp = self.client.post(url, registration_data)
        assert resp.status_code == 400
        assert resp.data['email']
        assert str(resp.data['email']) == 'A User with that email address already exists.'

    def test_user_update_password(self):
        current_password = 'SamTheGardener12!'
        new_password = 'SamTheHero12!'
        user = UserFactory(password=make_password(current_password))
        client = self.get_client(user)
        url = reverse('api:password-change')
        update_data = {
            'current_password': current_password,
            'new_password': new_password
        }
        resp = client.put(url, update_data)
        assert resp.status_code == 200
        assert resp.data['status'] == 'success'
        assert resp.data['message'] == 'Your password has successfully been updated.'

    def test_user_update_password_validation(self):
        current_password = new_password = 'SamTheGardener12!'
        user = UserFactory(password=make_password(current_password))
        client = self.get_client(user)
        url = reverse('api:password-change')
        update_data = {
            'current_password': current_password,
            'new_password': new_password
        }
        resp = client.put(url, update_data)
        assert resp.status_code == 400
        assert str(resp.data['new_password'][0]) == 'New password matches current password.'

    # def test_user_update():
    # client = self.get_client(user)
    #     # Implement update functionality
    #     pass
