import datetime
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from factory import SubFactory
from factory.django import DjangoModelFactory

from work_tracker.apps.tracker.enums import EntryStatus
from work_tracker.apps.tracker.models import Company, Entry, Project, Task
from work_tracker.apps.users.models import User


class SuperUserFactory(DjangoModelFactory):
    email = 'gandalftheadmin@test.com'
    first_name = 'Gandalf'
    last_name = 'Stormcrow'
    is_superuser = True
    is_staff = True
    _PASSWORD = 'FlyYouFools111!'
    password = make_password(_PASSWORD)

    @classmethod
    def _after_postgeneration(cls, obj, create, results=None):
        obj._PASSWORD = cls._PASSWORD

    class Meta:
        model = User
        django_get_or_create = ("email",)


class UserFactory(SuperUserFactory):
    email = 'samwisethebrave@test.com'
    first_name = 'Samwise'
    last_name = 'Gamgee'
    is_superuser = False
    is_staff = False
    rate = Decimal(10)


class CompanyFactory(DjangoModelFactory):
    name = "Mordor, Inc."
    description = "Split referring so Valar outrunning madman determined. Really wisest explain wounds aren't " \
                  "Dragon-Slayer. Misplaced different searching fleet Sauron's burns lines."

    class Meta:
        model = Company


class ProjectFactory(DjangoModelFactory):
    company = SubFactory(CompanyFactory)
    name = "Deliver the precious"
    description = "Awoke board carried wane stirring Frodo's rather crowned ill-favored! A wizard is never late, " \
                  "Frodo Baggins. Nor is he early. He arrives precisely when he means to. Pelennor guess don't seek"

    class Meta:
        model = Project


class TaskFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    project = SubFactory(ProjectFactory)
    name = "To Rivendell"
    code = "Rivendell-1"
    description = "The dark fire will not avail you, flame of Udun! Forbids wait stone dissuade first Ringwraiths " \
                  "protuberance tidings watch sit. Pines tombs before mercy gathering Lake-town endured."

    class Meta:
        model = Task


class EntryFactory(DjangoModelFactory):
    task = SubFactory(TaskFactory)
    comment = "Ringwraiths delayed process."
    start_time = (timezone.now() - datetime.timedelta(hours=3))
    end_time = timezone.now()
    status = EntryStatus.COMPLETE
    total_time = (3 * 3600)
    hours = Decimal(3)
    bill = Decimal(30)

    class Meta:
        model = Entry
