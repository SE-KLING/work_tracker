from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from work_tracker.apps.api.mixins import ActionSerializerMixin
from work_tracker.apps.tracker.api import serializers
from work_tracker.apps.tracker.models import Entry


class EntryViewSet(ActionSerializerMixin, ModelViewSet):
    basename = "entry"
    serializer_class = serializers.EntryListSerializer
    action_serializers = {
        "retrieve": serializers.EntryDetailSerializer,
        "create": serializers.EntryCreateSerializer,
        "update": serializers.EntryUpdateSerializer,
        "manualentry": serializers.EntryManualCreateSerializer,
    }

    def get_queryset(self):
        user = self.request.user
        return Entry.objects.select_related('task').filter(task__user=user).order_by("created_at", "status")

    def get_object(self):
        entry = get_object_or_404(Entry, pk=self.kwargs.get("pk", ""))
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
