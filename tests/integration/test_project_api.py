from rest_framework.test import APITestCase

from tests import factories
from tests.utils import JWTMixin
from work_tracker.apps.tracker.models import Project
from work_tracker.apps.users.models import User


class ProjectAPITestCase(APITestCase, JWTMixin):

    def setUp(self):
        self.base_url = '/api/project/'
        self.user = factories.UserFactory()
        self.user_1 = factories.UserFactory(email='merrythehorserider@test.com', name='Merry', last_name='Brandybuck')
        self.staff_user = factories.UserFactory(email='aragorn@test.com', is_staff=True, is_superuser=True)
        self.client = self.get_client(self.user)

        self.company = factories.CompanyFactory()
        self.project = factories.ProjectFactory(company=self.company)
        users = User.objects.filter(is_superuser=False)
        self.project.users.set(users)

        self.create_data = {
            'company_id': self.company.pk.hex,
            'users': [self.user.pk, self.user_1.pk],
            'name': 'Protect Fangorn',
            'description': "Search Treebeard crops pupil dreams hunter canting bloodline nervous? Don't you leave "
                           "him, Samwise Gamgee. Secure bid dangerous relevant cliff jambags Gimli then bears gallop."
        }

    def test_project_detail(self):
        url = f'{self.base_url}{self.project.pk.hex}/'
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.data['company_id'] == str(self.company.pk)
        assert resp.data['users']
        for user in resp.data['users']:
            assert user['id'] in self.project.users.values_list('id', flat=True)

    def test_project_list(self):
        factories.ProjectFactory(company=self.company, name='Traverse Moria')
        resp = self.client.get(self.base_url)
        assert resp.status_code == 200
        assert len(resp.data) == Project.objects.count()

    def test_project_create(self):
        client = self.get_client(self.staff_user)
        resp = client.post(self.base_url, self.create_data)
        assert resp.status_code == 201
        assert resp.data
        assert Project.objects.filter(pk=resp.data['id']).exists()
        project = Project.objects.get(pk=resp.data['id'])
        assert project.company == self.company
        assert project.users.count() == 2

    def test_project_create_validation(self):
        # Assert non-super/staff User may not create projects
        resp = self.client.post(self.base_url, self.create_data)
        assert resp.status_code == 403
        assert str(resp.data['detail']) == 'Only staff users may access this functionality.'

    def test_project_update(self):
        client = self.get_client(self.staff_user)
        url = f'{self.base_url}{self.project.pk.hex}/'
        data = {
            'name': 'Deliver the one ring.',
            'description': 'This has been updated.',
        }
        resp = client.put(url, data)
        assert resp.status_code == 200
        self.project.refresh_from_db()
        assert self.project.description == data['description']
        assert self.project.name == data['name']

    def test_project_update_validation(self):
        # Assert non-super/staff User may not update projects
        url = f'{self.base_url}{self.project.pk.hex}/'
        data = {
            'name': 'Deliver the one ring.',
            'description': 'This has been updated.',
        }
        resp = self.client.put(url, data)
        assert resp.status_code == 403
        assert str(resp.data['detail']) == 'Only staff users may access this functionality.'
