from uuid import uuid4

from django.db import models
from enumfields import EnumIntegerField

from work_tracker.apps.tracker.enums import EntryStatus, TaskStatus, TaskType
from work_tracker.apps.users.models import AmountField, TimeStampedModel, User


class Company(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class Project(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    users = models.ManyToManyField(User, related_name="projects")
    company = models.ForeignKey(Company, related_name="projects", on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Task(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    user = models.ForeignKey(User, related_name="tasks", on_delete=models.PROTECT)
    project = models.ForeignKey(Project, related_name="tasks", on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = EnumIntegerField(TaskType, default=TaskType.FEATURE)
    status = EnumIntegerField(TaskStatus, default=TaskStatus.NEW)

    class Meta:
        ordering = ("status",)

    def __str__(self):
        return f"{self.code} | {self.name}"


class Entry(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4)
    task = models.ForeignKey(Task, related_name="entries", on_delete=models.CASCADE)
    comment = models.TextField(blank=True)
    start_time = models.DateTimeField()
    pause_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    status = EnumIntegerField(EntryStatus, default=EntryStatus.ACTIVE)
    total_time = models.PositiveIntegerField(default=0)
    hours = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    bill = AmountField(default=0)

    class Meta:
        ordering = ("start_time",)
        verbose_name_plural = "Entries"

    def __str__(self):
        return (
            f"Entry by {self.task.user.email} for {self.task.code} created on "
            f'{self.created_at.strftime("%Y-%m-%d %H:%M:%S")}'
        )
