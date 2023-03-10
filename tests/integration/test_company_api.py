from rest_framework.test import APITestCase

from tests import factories
from tests.utils import JWTMixin
from work_tracker.apps.tracker.models import Company


class CompanyAPITestCase(APITestCase, JWTMixin):

    def setUp(self):
        self.base_url = '/api/company/'
        self.user = factories.UserFactory()
        self.staff_user = factories.UserFactory(email='aragorn@test.com', is_staff=True, is_superuser=True)
        self.client = self.get_client(self.user)
        self.company = factories.CompanyFactory()
        factories.CompanyFactory(name='Gondor, Inc.')

    def test_company_detail(self):
        factories.ProjectFactory(company=self.company)
        factories.ProjectFactory(company=self.company)

        url = f'{self.base_url}{self.company.pk.hex}/'
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.data['projects']
        assert len(resp.data['projects']) == 2

    def test_company_list(self):
        resp = self.client.get(self.base_url)
        assert resp.status_code == 200
        assert len(resp.data) == Company.objects.count()

    def test_company_create(self):
        client = self.get_client(self.staff_user)
        data = {
            'name': 'Rohan, Inc.',
            'description': "One Ring to rule them all. Place Bracegirdles bonds! Moved heal glass treachery "
                           "caretaker gems dominion mark Aragorn.",
        }
        resp = client.post(self.base_url, data)
        assert resp.status_code == 201

    def test_company_create_validation(self):
        # Assert non-super/staff User may not create companies
        data = {
            'name': 'Rohan, Inc.',
            'description': "One Ring to rule them all. Place Bracegirdles bonds! Moved heal glass treachery "
                           "caretaker gems dominion mark Aragorn.",
        }
        resp = self.client.post(self.base_url, data)
        assert resp.status_code == 403
        assert str(resp.data['detail']) == 'Only staff users may access this functionality.'

    def test_company_update(self):
        client = self.get_client(self.staff_user)
        url = f'{self.base_url}{self.company.pk.hex}/'
        data = {
            'description': 'This has been updated.',
            'name': 'Updated Company',
        }
        resp = client.put(url, data)
        assert resp.status_code == 200
        self.company.refresh_from_db()
        assert self.company.description == data['description']
        assert self.company.name == data['name']

    def test_company_update_validation(self):
        # Assert non-super/staff User may not update companies
        url = f'{self.base_url}{self.company.pk.hex}/'
        data = {
            'description': 'This has been updated.',
            'name': 'Updated Company',
        }
        resp = self.client.put(url, data)
        assert resp.status_code == 403
        assert str(resp.data['detail']) == 'Only staff users may access this functionality.'
