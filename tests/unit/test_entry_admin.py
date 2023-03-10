import datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tests import factories
from tests.factories import SuperUserFactory, UserFactory
from work_tracker.apps.tracker.enums import EntryStatus
from work_tracker.apps.tracker.models import Entry
from work_tracker.apps.users.models import User


class TestEntryAdmin(TestCase):

    def setUp(self):
        admin_user = SuperUserFactory()
        self.client.login(email=admin_user.email, password=admin_user._PASSWORD)

        self.user = UserFactory()
        project = factories.ProjectFactory()
        self.task = factories.TaskFactory(user=self.user)
        users = User.objects.filter(is_superuser=False)
        project.users.set(users)

    def test_entry_create(self):
        hour_offset = 2
        start_dt = (timezone.now() - datetime.timedelta(hours=hour_offset))
        end_dt = timezone.now()
        data = {
            'task': self.task.pk.hex,
            'start_time_0': start_dt.date(),
            'start_time_1': start_dt.time(),
            'end_time_0': end_dt.date(),
            'end_time_1': end_dt.time(),
            'comment': "Ring delivered."
        }
        self.client.post(reverse('admin:tracker_entry_add'), data)
        assert Entry.objects.filter(task=self.task).exists()

        entry = Entry.objects.first()
        assert all([entry.total_time, entry.hours, entry.bill, entry.status])
        assert entry.status == EntryStatus.COMPLETE
        assert entry.total_time == (hour_offset * 3600)
        assert entry.hours == round(Decimal(hour_offset), 6)
        assert entry.bill == round(entry.hours * self.user.rate, 2)

    def test_entry_create_validation(self):
        # Test invalid start_time/end_time
        now = timezone.now()
        start_dt = now
        end_dt = (now - datetime.timedelta(hours=2))
        data = {
            'task': self.task.pk.hex,
            'start_time_0': start_dt.date(),
            'start_time_1': start_dt.time(),
            'end_time_0': end_dt.date(),
            'end_time_1': end_dt.time(),
            'comment': "Ring delivered."
        }
        resp = self.client.post(reverse('admin:tracker_entry_add'), data)
        form_error = resp.context['adminform'].form.errors
        assert form_error == {'start_time': ["An Entry's start time may not exceed its end time."]}
        assert not Entry.objects.filter(task=self.task).exists()

        # Test start_time/end_time greater than current time
        start_dt = (now + datetime.timedelta(hours=2))
        end_dt = (now + datetime.timedelta(hours=3))
        data = {
            'task': self.task.pk.hex,
            'start_time_0': start_dt.date(),
            'start_time_1': start_dt.time(),
            'end_time_0': end_dt.date(),
            'end_time_1': end_dt.time(),
            'comment': "Ring delivered."
        }
        resp = self.client.post(reverse('admin:tracker_entry_add'), data)
        form_error = resp.context['adminform'].form.errors
        assert form_error['__all__'] == ['The selected start_time/end_time values may not exceed the current time.']
