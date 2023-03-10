from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from work_tracker.apps.api.components.tracker import serializers
from work_tracker.apps.api.mixins import ActionSerializerMixin
from work_tracker.apps.api.permissions import IsAuthorisedUser, ProjectSpecificTasks, UserSpecificEntries
from work_tracker.apps.tracker.models import Company, Entry, Project, Task


class CompanyViewSet(ActionSerializerMixin, ModelViewSet):
    basename = "company"
    serializer_class = serializers.CompanyListSerializer
    permission_classes = (IsAuthenticated, IsAuthorisedUser)
    action_serializers = {
        "retrieve": serializers.CompanyDetailSerializer,
        "create": serializers.CompanyCreateSerializer,
        "update": serializers.CompanyUpdateSerializer,
    }

    def get_queryset(self):
        return Company.objects.prefetch_related('projects').all()

    def get_object(self):
        company = get_object_or_404(Company, pk=self.kwargs.get("pk", ""))
        return company


class ProjectViewSet(ActionSerializerMixin, ModelViewSet):
    basename = "project"
    serializer_class = serializers.ProjectListSerializer
    permission_classes = (IsAuthenticated, IsAuthorisedUser)
    action_serializers = {
        "retrieve": serializers.ProjectDetailSerializer,
        "create": serializers.ProjectCreateSerializer,
        "update": serializers.ProjectUpdateSerializer,
    }

    def get_queryset(self):
        return Project.objects.prefetch_related('tasks').all()

    def get_object(self):
        project = get_object_or_404(Project, pk=self.kwargs.get("pk", ""))
        return project

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


class EntryViewSet(ActionSerializerMixin, ModelViewSet):
    basename = "entry"
    serializer_class = serializers.EntryListSerializer
    permission_classes = (IsAuthenticated, UserSpecificEntries)
    action_serializers = {
        "retrieve": serializers.EntryDetailSerializer,
        "create": serializers.EntryCreateSerializer,
        "update": serializers.EntryUpdateSerializer,
        "manualentry": serializers.EntryManualCreateSerializer,
    }

    def get_queryset(self):
        user = self.request.user
        return Entry.objects.select_related("task").filter(task__user=user).order_by("created_at", "status")

    def get_object(self):
        entry = get_object_or_404(Entry, pk=self.kwargs.get("pk", ""))
        self.check_object_permissions(self.request, entry)
        return entry

    @action(methods=["POST"], detail=False)
    def manualentry(self, request, *args, **kwargs):
        """
        Endpoint for creation of Manual time entries, where user can specify start and end time of an entry.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskViewSet(ActionSerializerMixin, ModelViewSet):
    basename = "project"
    serializer_class = serializers.TaskListSerializer
    permission_classes = (IsAuthenticated, IsAuthorisedUser, ProjectSpecificTasks)
    action_serializers = {
        "retrieve": serializers.TaskDetailSerializer,
        "create": serializers.TaskCreateSerializer,
        "update": serializers.TaskUpdateSerializer,
    }

    def get_queryset(self):
        return Task.objects.select_related('user', 'project').all()

    def get_object(self):
        project = get_object_or_404(Task, pk=self.kwargs.get("pk", ""))
        self.check_object_permissions(self.request, project)
        return project

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)
