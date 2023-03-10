from copy import deepcopy
from uuid import uuid4

from rest_framework.test import APITestCase

from tests import factories
from tests.utils import JWTMixin
from work_tracker.apps.tracker.enums import EntryStatus, TaskStatus, TaskType
from work_tracker.apps.tracker.models import Task


class TaskAPITestCase(APITestCase, JWTMixin):

    def setUp(self):
        self.base_url = '/api/task/'
        self.user = factories.UserFactory()
        self.staff_user = factories.UserFactory(email='aragorn@test.com', is_staff=True, is_superuser=True)
        self.client = self.get_client(self.user)

        self.company = factories.CompanyFactory()
        self.project = factories.ProjectFactory(company=self.company)
        self.project.users.add(self.user)
        self.task = factories.TaskFactory(project=self.project, user=self.user)
        self.create_data = {
            'user_id': self.user.pk.hex,
            'project_id': self.project.pk.hex,
            'name': 'Collect mushrooms',
            'code': 'Mushroom',
            'type': TaskType.FEATURE.name,
            'description': "Wine pages towers denying Smeagol's only bites ancient fairer. "
                           "Protected able slay throttle Háma written unsavory stink bay ragged war gibbet. "
                           "Beasts Andros onto appears summoning sweeps six farewell tomorrow's stealth warned!"
        }

    def test_task_detail(self):
        factories.EntryFactory(task=self.task, status=EntryStatus.COMPLETE)
        factories.EntryFactory(task=self.task, status=EntryStatus.COMPLETE)

        url = f'{self.base_url}{self.task.pk.hex}/'
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.data['project_id'] == str(self.task.project.pk)
        assert resp.data['entries']
        assert len(resp.data['entries']) == 2

    def test_task_detail_validation(self):
        user = factories.UserFactory(email='gollum@test.com')
        project = factories.ProjectFactory(name='Collect mushrooms')
        project.users.add(user)
        project.save()
        task = factories.TaskFactory(project=project, user=user)

        # Assert users that do not belong to the entry associated project can not access its entries.
        url = f'{self.base_url}{task.pk.hex}/'
        resp = self.client.get(url)
        assert resp.status_code == 403
        assert str(resp.data['detail']) == 'You cannot access Task details for tasks not assigned to you.'

        # Assert adding client to the entry associated project circumvents permission error
        project.users.add(self.user)
        project.save()
        resp = self.client.get(url)
        assert resp.status_code == 200

    def test_task_list(self):
        project = factories.ProjectFactory(company=self.company, name='Traverse Moria')
        factories.TaskFactory(user=self.user, name='Through Moria', code='Moria-1', project=project)

        resp = self.client.get(self.base_url)
        assert resp.status_code == 200
        assert len(resp.data) == Task.objects.count()

    def test_task_create(self):
        client = self.get_client(self.staff_user)
        resp = client.post(self.base_url, self.create_data)
        assert resp.status_code == 201
        assert Task.objects.filter(pk=resp.data['id']).exists()
        task = Task.objects.get(pk=resp.data['id'])
        assert task.user == self.user
        assert task.project == self.project
        assert task.status == TaskStatus.NEW

    def test_task_create_validation(self):
        # Assert non-super/staff User may not create tasks
        resp = self.client.post(self.base_url, self.create_data)
        assert resp.status_code == 403
        assert str(resp.data['detail']) == 'Only staff users may access this functionality.'

        # Assert assigning task to user not in involved in project
        data = deepcopy(self.create_data)
        client = self.get_client(self.staff_user)
        user = factories.UserFactory(email='merrythehorserider@test.com')
        data['user_id'] = user.pk.hex
        resp = client.post(self.base_url, data)
        assert resp.status_code == 400
        assert str(resp.data['non_field_errors'][0]) == "You can only assign tasks to user's associated with " \
                                                        "the task project."

        # Assert non-existent user.id used in request
        data = deepcopy(self.create_data)
        data['user_id'] = uuid4().hex
        resp = client.post(self.base_url, data)
        assert resp.status_code == 400
        assert str(resp.data['non_field_errors'][0]) == 'The selected User does not exist.'

        # Assert non-existent project.id used in request
        data = deepcopy(self.create_data)
        data['project_id'] = uuid4().hex
        resp = client.post(self.base_url, data)
        assert resp.status_code == 400
        assert str(resp.data['non_field_errors'][0]) == 'The selected Project does not exist.'

    def test_task_update(self):
        client = self.get_client(self.staff_user)
        url = f'{self.base_url}{self.task.pk.hex}/'
        data = {
            'description': 'This has been updated.',
            'status': TaskStatus.COMPLETED.name,
        }
        resp = client.put(url, data)
        assert resp.status_code == 200
        self.task.refresh_from_db()
        assert self.task.description == data['description']
        assert self.task.status.name == data['status']

    def test_task_update_validation(self):
        # Assert non-super/staff User may not update tasks
        url = f'{self.base_url}{self.task.pk.hex}/'
        data = {
            'description': 'This has been updated.',
            'status': TaskStatus.COMPLETED.name,
        }
        resp = self.client.put(url, data)
        assert resp.status_code == 403
        assert str(resp.data['detail']) == 'Only staff users may access this functionality.'
