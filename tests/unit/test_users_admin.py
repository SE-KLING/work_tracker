from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from tests import factories
from work_tracker.apps.users.models import User


class TestUserAdmin(TestCase):

    def setUp(self):
        user = factories.SuperUserFactory()
        self.client.login(email=user.email, password=user._PASSWORD)

    def test_user_create(self):
        sign_up_data = {
            'email': 'pippin@test.com',
            'password1': 'FoolOfATook00!',
            'password2': 'FoolOfATook00!',
            'first_name': 'Peregrin',
            'last_name': 'Took',
            'rate': Decimal(10),
            'is_active': True
        }
        self.client.post(reverse('admin:users_user_add'), sign_up_data)

        assert User.objects.filter(email=sign_up_data['email']).exists()
        user = User.objects.get(email=sign_up_data['email'])
        assert user.rate == sign_up_data['rate']
        assert user.name == ' '.join(map(str, [sign_up_data['first_name'], sign_up_data['last_name']])).strip()

    def test_user_delete(self):
        user = factories.UserFactory()
        assert user.is_active
        assert not user.deactivated_at

        self.client.post(reverse('admin:users_user_delete', args=[user.pk]), {'post': 'yes'})
        # Assert if User still exists in DB
        assert User.objects.filter(pk=user.pk).exists()
        # Assert if soft delete was successful
        user.refresh_from_db()
        assert not user.is_active
        assert user.deactivated_at
