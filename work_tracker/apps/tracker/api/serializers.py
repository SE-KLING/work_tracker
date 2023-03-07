from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from work_tracker.apps.api.fields import EnumField
from work_tracker.apps.tracker.enums import EntryAction, EntryStatus
from work_tracker.apps.tracker.models import Entry


def calculate_billables(
    entry: Entry, start_time: datetime, end_time: datetime
) -> Entry:
    """
    Calculate and update total_time, hours, bill of current Entry instance based off of specified
    start_time and end_time.

    Returns:
        Entry: Updated Entry instance.
    """
    user = entry.task.user
    total_time = (end_time - start_time).total_seconds()
    hours = round(total_time / 3600, 6)
    bill = round(Decimal(hours) * user.rate, 2)

    # Update instance fields with calculated values.
    entry.total_time += total_time
    entry.hours += hours
    entry.bill += bill
    return entry


class BaseEntrySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    task_id = serializers.UUIDField(source="task.id")
    user = serializers.ReadOnlyField(source="task.user.email")
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    pause_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    status = EnumField(EntryStatus)
    hours = serializers.DecimalField(max_digits=10, decimal_places=6)
    bill = serializers.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        model = Entry
        fields = (
            "id",
            "task_id",
            "user",
            "start_time",
            "pause_time",
            "end_time",
            "status",
            "total_time",
            "hours",
            "bill",
        )
        read_only_fields = fields


class EntryListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    task_id = serializers.UUIDField(read_only=True, source="task.id")
    user = serializers.ReadOnlyField(source="task.user.email")
    start_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    pause_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    end_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    status = EnumField(EntryStatus, read_only=True)
    hours = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)
    bill = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = Entry
        fields = (
            "id",
            "task_id",
            "user",
            "start_time",
            "pause_time",
            "end_time",
            "status",
            "total_time",
            "hours",
            "bill",
        )


class EntryCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    task_id = serializers.UUIDField()
    start_time = serializers.DateTimeField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = self.context["request"].user

    #     project_pks = list(user.projects.values_list('pk', flat=True))
    #     tasks_qs = Task.objects.select_related('project').filter(project__pk__in=project_pks)
    #     self.fields['tasks'] = serializers.PrimaryKeyRelatedField(many=True, queryset=tasks_qs)

    @staticmethod
    def validate_start_time(value):
        now = timezone.now()
        if value > now:
            raise serializers.ValidationError(
                "An Entry's start time may not exceed the current time."
            )
        return value

    def validate_task_id(self, value):
        user_tasks = self.user.entries.values_list("id", flat=True)
        if value not in user_tasks:
            raise serializers.ValidationError(
                "The selected task has not been assigned to you."
            )
        return value

    class Meta:
        model = Entry
        fields = ("id", "task_id", "start_time")


class EntryUpdateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    task_id = serializers.UUIDField(read_only=True)
    action = EnumField(EntryAction)
    entry_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    total_time = serializers.IntegerField(read_only=True)
    hours = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)

    def __init__(self, instance=None, data=serializers.empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)
        self.user = self.context["request"].user
        if instance.status == EntryStatus.COMPLETE:
            raise serializers.ValidationError(
                "You cannot edit an already completed entry."
            )
        self.entry = instance

    def validate(self, attrs):
        action = attrs["action"].name
        status = self.entry.status
        if action == "PAUSE" and status != EntryStatus.ACTIVE:
            raise serializers.ValidationError(
                "You cannot pause an entry that is not active."
            )
        elif action == "RESUME" and status != EntryStatus.PAUSED:
            raise serializers.ValidationError(
                "You cannot resume an already active entry."
            )
        return attrs

    def validate_entry_time(self, value):
        if value < self.entry.start_time:
            raise serializers.ValidationError(
                "An Entry's pause/completion time cannot precede its start time."
            )
        return value

    def update(self, instance, validated_data):
        action = validated_data["action"]
        entry_time = validated_data["entry_time"]
        # If user is pausing current entry
        if action == "PAUSE":
            instance.pause_time = entry_time
            instance.status = EntryStatus.PAUSED
            instance = calculate_billables(instance, instance.start_time, entry_time)
        # If user is resuming a paused entry
        elif action == "UNPAUSE":
            instance.start_time = entry_time
            instance.pause_time = None
            instance.status = EntryStatus.ACTIVE
        # If user is completing an entry
        else:
            instance.end_time = entry_time
            instance.status = EntryStatus.COMPLETE
            instance = calculate_billables(instance, instance.start_time, entry_time)
        instance.save()
        return instance

    class Meta:
        model = Entry
        fields = (
            "id",
            "task_id",
            "action",
            "entry_time",
            "total_time",
            "hours",
            "bill",
        )


class EntryDetailSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    task_id = serializers.ReadOnlyField(source="task.id")
    start_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    pause_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    end_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    status = EnumField(EntryStatus, read_only=True)
    hours = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)
    bill = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)


class EntryManualCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    task_id = serializers.UUIDField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    comment = serializers.CharField()
    status = EnumField(EntryStatus, read_only=True)
    hours = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)
    bill = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    def validate_task_id(self, value):
        user_tasks = self.user.entries.values_list("id", flat=True)
        if value not in user_tasks:
            raise serializers.ValidationError(
                "The selected task has not been assigned to you."
            )
        return value

    def validate(self, attrs):
        if attrs["end_time"] <= attrs["start_time"]:
            raise serializers.ValidationError(
                "The selected end time must be greater than the selected start time."
            )
        return attrs

    def create(self, validated_data):
        entry = super().create(validated_data)
        updated_entry = calculate_billables(entry, entry.start_time, entry.end_time)
        updated_entry.save()
        return updated_entry

    class Meta:
        model = Entry
        fields = (
            "id",
            "task_id",
            "start_time",
            "end_time",
            "comment",
            "status",
            "total_time",
            "hours",
            "bill",
        )
        read_only_fields = ("id", "status", "total_time", "hours", "bill")
