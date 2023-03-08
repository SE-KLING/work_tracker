from django.utils import timezone
from rest_framework import serializers

from work_tracker.apps.api.fields import EnumField
from work_tracker.apps.tracker.enums import EntryAction, EntryStatus
from work_tracker.apps.tracker.models import Entry
from work_tracker.apps.utils import calculate_billables


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
        fields = ("id", "task_id", "user", "start_time", "pause_time", "end_time", "status", "total_time", "hours",
                  "bill")


class EntryDetailSerializer(EntryListSerializer):
    pass


class EntryCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    task_id = serializers.UUIDField()
    start_time = serializers.DateTimeField()
    status = EnumField(EntryStatus, read_only=True)

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
        user = self.context['request'].user
        user_tasks = user.entries.values_list("id", flat=True)
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
    action = EnumField(EntryAction, write_only=True)
    entry_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", write_only=True)
    total_time = serializers.IntegerField(read_only=True)
    hours = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)

    def __init__(self, instance=None, data=serializers.empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)
        self.user = self.context["request"].user
        if instance.status == EntryStatus.COMPLETE:
            raise serializers.ValidationError("You cannot edit an already completed entry.")
        self.entry = instance

    def validate(self, attrs):
        action = attrs["action"].name
        status = self.entry.status
        # If an entry is either already paused or completed, a user should not be able to pause the entry again.
        if action == "PAUSE" and status != EntryStatus.ACTIVE:
            raise serializers.ValidationError(
                "You cannot pause an entry that is not active."
            )
        # If an entry is already active, a user should not be able to resume the entry again.
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
        """
        The "EntryUpdate" View encompasses the functionality to pause, resume or complete an existing entry.
        The applicable action ("RESUME", "PAUSE", "COMPLETE") is paused within the request payload and determines how
        the entry instance will be updated.
        """
        action = validated_data["action"]
        entry_time = validated_data["entry_time"]
        # If user is pausing current entry
        if action == EntryAction.PAUSE:
            instance.pause_time = entry_time
            instance.status = EntryStatus.PAUSED
            instance = calculate_billables(instance, instance.start_time, entry_time)
        # If user is resuming a paused entry
        elif action == EntryAction.RESUME:
            instance.start_time = entry_time
            instance.pause_time = None
            instance.status = EntryStatus.ACTIVE
        # If user is completing an entry
        else:
            # If entry is active and has not been paused, no calculations will need to be done.
            if instance.status == EntryStatus.ACTIVE:
                instance = calculate_billables(instance, instance.start_time, entry_time)
            instance.end_time = entry_time
            instance.status = EntryStatus.COMPLETE
        instance.save()
        return instance

    class Meta:
        model = Entry
        fields = ("id", "task_id", "action", "entry_time", "total_time", "hours", "bill")


class EntryManualCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    task_id = serializers.UUIDField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    comment = serializers.CharField(required=False)
    status = EnumField(EntryStatus, read_only=True)
    total_time = serializers.IntegerField(read_only=True)
    hours = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)
    bill = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    def validate_task_id(self, value):
        user = self.context['request'].user
        user_tasks = user.entries.values_list("id", flat=True)
        if value not in user_tasks:
            raise serializers.ValidationError(
                "The selected task has not been assigned to you."
            )
        return value

    def validate(self, attrs):
        now = timezone.now()
        start = attrs["start_time"]
        end = attrs["end_time"]
        # Ensure user has not selected datetime beyond current time.
        if start >= now or end > now:
            raise serializers.ValidationError(
                "The selected start_time/end_time values may not exceed the current time."
            )
        # Ensure user has not selected a start_time greater than the end_time.
        if start >= end:
            raise serializers.ValidationError(
                {"start_time": "An Entry's start time may not exceed its end time."}
            )
        return attrs

    def create(self, validated_data):
        entry = super().create(validated_data)
        updated_entry = calculate_billables(entry, entry.start_time, entry.end_time)
        updated_entry.status = EntryStatus.COMPLETE
        updated_entry.save()
        return updated_entry

    class Meta:
        model = Entry
        fields = ("id", "task_id", "start_time", "end_time", "comment", "status", "total_time", "hours", "bill")
