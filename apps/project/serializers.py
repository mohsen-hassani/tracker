from rest_framework import serializers
from .models import Project, Task


class ProjectSeriailzer(serializers.ModelSerializer):
    owner = serializers.CharField(source='created_by', read_only=True)

    class Meta:
        model = Project
        fields = ('uuid', 'title', 'slug', 'is_deleted', 'created_at', 'updated_at', 'owner')
        read_only_fields = ('slug', )


class TaskSerializer(serializers.ModelSerializer):
    project = ProjectSeriailzer(many=False, read_only=True)
    is_running = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ('uuid', 'project', 'title', 'is_running', 'duration', 'created_at', 'updated_at')

    def get_is_running(self, obj):
        return obj.is_running()

    def get_duration(self, obj):
        return obj.get_total_spent_time()
    