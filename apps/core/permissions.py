from rest_framework.permissions import BasePermission

class IsObjectCreator(BasePermission):
    """Check if user is owner of the object"""
    def __init__(self, field=None):
        self.field = field or 'created_by'

    def has_object_permission(self, request, view, obj):
        prev_result = super().has_object_permission(request, view, obj)
        fields = self.field.split('__')
        for field in fields:
            obj = getattr(obj, field)
        result =  obj == request.user
        return prev_result & result

