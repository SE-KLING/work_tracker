class ActionSerializerMixin:
    """
    Support to configure a Serializer Class per 'action'
    """

    action_serializers = {}
    action_meta = ("create", "update", "list")

    def get_serializer_class(self):
        action = getattr(self, "action", None)
        if action == "metadata":
            for a in self.action_meta:
                if a in self.action_serializers:
                    action = a
                    break
        if action and action in self.action_serializers:
            return self.action_serializers[action]
        else:
            return super().get_serializer_class()
