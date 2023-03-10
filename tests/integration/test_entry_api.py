import datetime
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from tests import factories
from tests.utils import JWTMixin
from work_tracker.apps.tracker.enums import EntryAction, EntryStatus
from work_tracker.apps.tracker.models import Entry


class EntryAPITestCase(APITestCase, JWTMixin):

    def setUp(self):
        self.base_url = '/api/entry/'
        self.user = factories.UserFactory()
        self.client = self.get_client(self.user)
        company = factories.CompanyFactory()
        project_1 = factories.ProjectFactory(company=company)
        project_2 = factories.ProjectFactory(company=company, name="Defend Helm's Deep")
        self.task_1 = factories.TaskFactory(user=self.user, project=project_1)
        self.task_2 = factories.TaskFactory(user=self.user, project=project_2, name='Look to the east', code='Siege-1')
        self.task_3 = factories.TaskFactory(user=factories.UserFactory(email='gollum@test.com'), project=project_1,
                                            name="What's potatoes", code='Rabbit-stew-1')

    def test_entry_list(self):
        # Create entries pertaining to tasks linked to User.
        factories.EntryFactory(task=self.task_1)
        factories.EntryFactory(task=self.task_2, comment='Gandalf arrived.')
        # Create additional entry for task not linked to User.
        factories.EntryFactory(task=self.task_3)

        resp = self.client.get(self.base_url)
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        for entry in resp.json():
            assert entry['user'] == self.user.email

    def test_entry_detail(self):
        entry = factories.EntryFactory(task=self.task_1)
        url = f'{self.base_url}{entry.pk.hex}/'

        resp = self.client.get(url)
        assert resp.status_code == 200
        assert all([resp.data['total_time'], resp.data['hours'], resp.data['bill']])

    def test_entry_detail_validation(self):
        entry = factories.EntryFactory(task=self.task_3)
        url = f'{self.base_url}{entry.pk.hex}/'

        resp = self.client.get(url)
        assert resp.status_code == 403
        assert str(resp.data['detail']) == 'You cannot access Entries for tasks not assigned to you.'

    def test_entry_create(self):
        data = {
            'start_time': timezone.now(),
            'task_id': self.task_1.id.hex
        }
        resp = self.client.post(self.base_url, data)
        assert resp.status_code == 201
        assert Entry.objects.filter(pk=resp.data['id'])
        entry = Entry.objects.get(pk=resp.data['id'])
        assert entry.status == EntryStatus.ACTIVE
        assert entry.total_time == entry.hours == entry.bill == 0

    def test_entry_create_validation(self):
        data = {
            'start_time': timezone.now() + datetime.timedelta(hours=1),
            'task_id': self.task_1.id.hex
        }

        resp = self.client.post(self.base_url, data)
        resp.status_code == 400
        assert resp.data['start_time']
        assert str(resp.data['start_time'][0]) == "An Entry's start time may not exceed the current time."

    def test_entry_pause(self):
        entry = factories.EntryFactory(task=self.task_1, status=EntryStatus.ACTIVE, total_time=0, hours=0, bill=0,
                                       end_time=None)
        hour_offset = 4
        entry_time = entry.start_time + datetime.timedelta(hours=hour_offset)
        data = {
            'task_id': entry.task.pk.hex,
            'action': EntryAction.PAUSE.name,
            'entry_time': entry_time
        }
        url = f'{self.base_url}{entry.pk.hex}/'

        resp = self.client.put(url, data)
        assert resp.status_code == 200

        entry.refresh_from_db()
        assert resp.data['total_time'] == (hour_offset * 3600)
        assert Decimal(resp.data['hours']) == round(Decimal(hour_offset), 6)
        assert Decimal(resp.data['bill']) == round(entry.hours * self.user.rate, 2)
        assert entry.status == EntryStatus.PAUSED

    def test_entry_pause_validation(self):
        entry = factories.EntryFactory(task=self.task_1, status=EntryStatus.PAUSED)
        data = {
            'task_id': entry.task.pk.hex,
            'action': EntryAction.PAUSE.name,
            'entry_time': entry.start_time + datetime.timedelta(hours=2)
        }
        url = f'{self.base_url}{entry.pk.hex}/'

        resp = self.client.put(url, data)
        assert resp.status_code == 400
        assert resp.data['non_field_errors']
        assert str(resp.data['non_field_errors'][0]) == 'You cannot pause an entry that is not active.'

    def test_entry_resume(self):
        entry = factories.EntryFactory(task=self.task_1, status=EntryStatus.PAUSED, pause_time=timezone.now(),
                                       end_time=None)
        entry_time = entry.pause_time + datetime.timedelta(hours=4)
        data = {
            'task_id': entry.task.pk.hex,
            'action': EntryAction.RESUME.name,
            'entry_time': entry_time
        }
        url = f'{self.base_url}{entry.pk.hex}/'

        resp = self.client.put(url, data)
        assert resp.status_code == 200

        entry.refresh_from_db()
        assert not entry.pause_time
        assert entry.start_time == entry_time

    def test_entry_resume_validation(self):
        entry = factories.EntryFactory(task=self.task_1, status=EntryStatus.ACTIVE, end_time=None)
        entry_time = entry.start_time + datetime.timedelta(hours=2)
        data = {
            'task_id': entry.task.pk.hex,
            'action': EntryAction.RESUME.name,
            'entry_time': entry_time
        }
        url = f'{self.base_url}{entry.pk.hex}/'
        resp = self.client.put(url, data)
        assert resp.status_code == 400
        assert str(resp.data['non_field_errors'][0]) == 'You cannot resume an already active entry.'

        entry.status = EntryStatus.PAUSED
        entry.save()
        entry_time = entry.start_time - datetime.timedelta(hours=2)
        data['entry_time'] = entry_time
        resp = self.client.put(url, data)
        assert resp.status_code == 400
        assert str(resp.data['entry_time'][0]) == "An Entry's pause/completion time cannot precede its start time."

    def test_entry_complete_from_active(self):
        entry = factories.EntryFactory(task=self.task_1, status=EntryStatus.ACTIVE, end_time=None, total_time=0,
                                       hours=0, bill=0,)
        hour_offset = 3
        entry_time = entry.start_time + datetime.timedelta(hours=hour_offset)
        data = {
            'task_id': entry.task.pk.hex,
            'action': EntryAction.COMPLETE.name,
            'entry_time': entry_time
        }
        url = f'{self.base_url}{entry.pk.hex}/'

        resp = self.client.put(url, data)
        assert resp.status_code == 200

        entry.refresh_from_db()
        assert all([entry.end_time, entry.total_time, entry.hours, entry.bill])
        assert resp.data['total_time'] == (hour_offset * 3600)
        assert Decimal(resp.data['hours']) == round(Decimal(hour_offset), 6)
        assert Decimal(resp.data['bill']) == round(entry.hours * self.user.rate, 2)
        assert entry.status == EntryStatus.COMPLETE

    def test_entry_complete_from_paused(self):
        now = timezone.now()
        pause_time = now - datetime.timedelta(hours=1)
        hour_offset = 3
        start_time = pause_time - datetime.timedelta(hours=hour_offset)
        entry = factories.EntryFactory(task=self.task_1, status=EntryStatus.PAUSED, start_time=start_time,
                                       end_time=None, pause_time=pause_time)
        data = {
            'task_id': entry.task.pk.hex,
            'action': EntryAction.COMPLETE.name,
            'entry_time': now
        }
        url = f'{self.base_url}{entry.pk.hex}/'

        resp = self.client.put(url, data)
        assert resp.status_code == 200
        # Because entry was saved from a paused state, no further calculations were done.
        assert resp.data['total_time'] == entry.total_time
        assert Decimal(resp.data['hours']) == entry.hours
        assert Decimal(resp.data['bill']) == entry.bill
        entry.refresh_from_db()
        assert entry.status == EntryStatus.COMPLETE

    def test_entry_complete_validation(self):
        entry = factories.EntryFactory(task=self.task_1, status=EntryStatus.COMPLETE)
        data = {
            'task_id': entry.task.pk.hex,
            'action': EntryAction.COMPLETE.name,
            'entry_time': timezone.now()
        }
        url = f'{self.base_url}{entry.pk.hex}/'

        resp = self.client.put(url, data)
        assert resp.status_code == 400
        assert str(resp.data[0]) == 'You cannot edit an already completed entry.'

    def test_entry_manual_create(self):
        end_time = timezone.now()
        hour_offset = 5
        start_time = end_time - datetime.timedelta(hours=hour_offset)
        data = {
            'start_time': start_time,
            'end_time': end_time,
            'task_id': self.task_1.id.hex
        }
        url = f'{self.base_url}manualentry/'

        resp = self.client.post(url, data)
        assert resp.status_code == 201

        assert Entry.objects.filter(pk=resp.data['id'])
        entry = Entry.objects.get(pk=resp.data['id'])
        assert entry.total_time == (hour_offset * 3600)
        assert entry.hours == round(Decimal(hour_offset), 6)
        assert entry.bill == round(entry.hours * self.user.rate, 2)
        assert entry.status == EntryStatus.COMPLETE

    def test_entry_manual_create_validation(self):
        now = timezone.now()
        # Add task_id that is not assigned to User
        data = {
            'start_time': now - datetime.timedelta(hours=2),
            'end_time': now,
            'task_id': self.task_3.id.hex
        }
        url = f'{self.base_url}manualentry/'

        resp = self.client.post(url, data)
        assert resp.status_code == 400
        assert str(resp.data['task_id'][0]) == 'The selected task has not been assigned to you.'

        # Test invalid start_time/end_time
        data = {
            'start_time': now,
            'end_time': now - datetime.timedelta(hours=2),
            'task_id': self.task_1.id.hex
        }
        url = f'{self.base_url}manualentry/'

        resp = self.client.post(url, data)
        assert resp.status_code == 400
        assert str(resp.data['start_time'][0]) == "An Entry's start time may not exceed its end time."

        # Test start_time/end_time greater than current time
        data = {
            'start_time': now + datetime.timedelta(hours=2),
            'end_time': now + datetime.timedelta(hours=3),
            'task_id': self.task_1.id.hex
        }
        url = f'{self.base_url}manualentry/'

        resp = self.client.post(url, data)
        assert resp.status_code == 400
        assert str(resp.data['non_field_errors'][0]) == 'The selected start_time/end_time values may not exceed ' \
                                                        'the current time.'
