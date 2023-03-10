from django.utils import timezone
from rest_framework import serializers

from work_tracker.apps.api.fields import EnumField
from work_tracker.apps.tracker.enums import EntryAction, EntryStatus, TaskStatus, TaskType
from work_tracker.apps.tracker.models import Company, Entry, Project, Task
from work_tracker.apps.users.models import User
from work_tracker.apps.utils import calculate_billables

# ENTRY SERIALIZERS


class EntryListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    task_id = serializers.UUIDField(read_only=True, source="task.id")
    user = serializers.ReadOnlyField(source="task.user.email")
    start_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    pause_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    end_time = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    status = EnumField(EntryStatus, read_only=True)

    class Meta:
        model = Entry
        fields = ("id", "task_id", "user", "start_time", "pause_time", "end_time", "status")


class EntryDetailSerializer(EntryListSerializer):
    hours = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)
    bill = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = Entry
        fields = ("id", "task_id", "user", "start_time", "pause_time", "end_time", "status", "total_time", "hours",
                  "bill")


class EntryCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    task_id = serializers.UUIDField()
    start_time = serializers.DateTimeField()
    status = EnumField(EntryStatus, read_only=True)

    @staticmethod
    def validate_start_time(value):
        now = timezone.now()
        if value > now:
            raise serializers.ValidationError(
                "An Entry's start time may not exceed the current time."
            )
        return value

    def validate_task_id(self, value):
        try:
            user = self.context['request'].user
            task = Task.objects.get(pk=value)
            if task.user != user:
                raise serializers.ValidationError("The selected task has not been assigned to you.")
        except Task.DoesNotExist:
            raise serializers.ValidationError("The selected task does not exist.")
        return value

    class Meta:
        model = Entry
        fields = ("id", "task_id", "start_time", "status")


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
            # If completing an already paused entry, take pause_time as end_time.
            else:
                instance.end_time = instance.pause_time
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
        user_tasks = user.tasks.values_list("id", flat=True)
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


# TASK SERIALIZERS

class TaskListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    project_id = serializers.UUIDField(read_only=True)
    project = serializers.CharField(read_only=True, source='project.name')
    name = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'user_id', 'project_id', 'project', 'name', 'code')


class TaskDetailSerializer(TaskListSerializer):
    description = serializers.CharField(read_only=True)
    type = EnumField(TaskType, read_only=True)
    status = EnumField(TaskStatus, read_only=True)
    entries = EntryDetailSerializer(read_only=True, many=True)

    class Meta:
        model = Task
        fields = ('id', 'user_id', 'project_id', 'project', 'name', 'code', 'description', 'type', 'status', 'entries')


class TaskCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField()
    project_id = serializers.UUIDField()
    name = serializers.CharField()
    code = serializers.CharField()
    description = serializers.CharField()
    type = EnumField(TaskType)

    class Meta:
        model = Task
        fields = ('id', 'user_id', 'project_id', 'name', 'code', 'description', 'type')

    def validate(self, attrs):
        try:
            user = User.objects.get(pk=attrs['user_id'])
            project = Project.objects.get(pk=attrs['project_id'])
            if user not in project.users.all():
                raise serializers.ValidationError(
                    "You can only assign tasks to user's associated with the task project."
                )
        except User.DoesNotExist:
            raise serializers.ValidationError('The selected User does not exist.')
        except Project.DoesNotExist:
            raise serializers.ValidationError('The selected Project does not exist.')
        return attrs


class TaskUpdateSerializer(TaskListSerializer):
    description = serializers.CharField(write_only=True)
    status = EnumField(TaskStatus, write_only=True)

    class Meta:
        model = Task
        fields = ('description', 'status')


# PROJECT SERIALIZERS


class ProjectListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'description')


class ProjectDetailSerializer(ProjectListSerializer):
    users = serializers.SerializerMethodField()
    company_id = serializers.UUIDField(read_only=True)
    company = serializers.CharField(read_only=True, source='company.name')

    # noinspection PyMethodMayBeStatic
    def get_users(self, obj):
        users = list(obj.users.values('id', 'email', 'name'))
        return users

    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'users', 'company_id', 'company')


class ProjectCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    company_id = serializers.UUIDField()
    users = serializers.PrimaryKeyRelatedField(many=True, write_only=True,
                                               queryset=User.objects.all().exclude(is_superuser=True, is_staff=True))
    name = serializers.CharField()
    description = serializers.CharField()

    class Meta:
        model = Project
        fields = ('id', 'company_id', 'users', 'name', 'description')

    def create(self, validated_data):
        users = validated_data.pop('users')
        project = Project.objects.create(**validated_data)
        for user in users:
            project.users.add(user)
        return project


class ProjectUpdateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    description = serializers.CharField()

    class Meta:
        model = Project
        fields = ('id', 'name', 'description')

# COMPANY SERIALIZERS


class CompanyListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)

    class Meta:
        model = Company
        fields = ('id', 'name', 'description')


class CompanyDetailSerializer(CompanyListSerializer):
    projects = serializers.SerializerMethodField()

    # noinspection PyMethodMayBeStatic
    def get_projects(self, obj):
        projects = list(obj.projects.values('id', 'name', 'description'))
        return projects

    class Meta:
        model = Company
        fields = ('id', 'name', 'description', 'projects')


class CompanyCreateSerializer(CompanyListSerializer):
    name = serializers.CharField()
    description = serializers.CharField()


class CompanyUpdateSerializer(serializers.ModelSerializer):
    pass

    class Meta:
        model = Company
        fields = '__all__'
