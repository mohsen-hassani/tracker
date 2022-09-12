from rest_framework import viewsets, response, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.core.permissions import IsObjectCreator
from apps.core.mixins import MultipleFieldLookupMixin
from .models import Project, Task
from .serializers import ProjectSeriailzer, TaskSerializer
from .services import StopAllTasksService, StartTaskService
from .exceptions import CuncurrentTaskException, NoRunningTaskFoundException


def is_task_creator():
    return IsObjectCreator('project__created_by')

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSeriailzer
    permission_classes = (IsAuthenticated, IsObjectCreator, )
    lookup_field = "uuid"

    def get_queryset(self):
        qs = Project.objects.user_projects(self.request.user)
        deleted = self.request.GET.get('deleted')
        if self.action != 'restore' and not deleted:
            qs = qs.non_deleted()
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(methods=['PATCH'], detail=True)
    def restore(self, request, uuid):
        obj = self.get_object()
        obj.restore()
        serializer = self.serializer_class(instance=obj)
        return response.Response(data=serializer.data)

    @action(methods=['PUT'], detail=True, url_path='stop-all-tasks')
    def stop_all_tasks(self, request, uuid):
        project = self.get_object()
        try:
            service = StopAllTasksService(project=project)
            stopped_tasks = service.execute()
            return response.Response({"stopped_tasks": stopped_tasks})
        except NoRunningTaskFoundException:
            return response.Response("No Running Task found", status=status.HTTP_204_NO_CONTENT)

class TaskViewSet(MultipleFieldLookupMixin, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, is_task_creator)
    serializer_class = TaskSerializer
    lookup_fields = ['project__uuid', 'uuid']
    lookup_field = 'uuid'

    def get_queryset(self):
        project = self._get_project()
        return Task.objects.filter(project__created_by=self.request.user, project=project)

    def perform_create(self, serializer):
        serializer.save(project=self._get_project())

    def _get_project(self):
        project_uuid = self.kwargs.get('project__uuid')
        return Project.objects.get(uuid=project_uuid)

    @action(methods=['PATCH'], detail=True)
    def start(self, request, project__uuid, uuid):
        task = self.get_object()
        try:
            service = StartTaskService(task=task)
            service.execute()
        except CuncurrentTaskException:
            return response.Response({'error': 'You cannot start multiple tasks at the same time'}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=True)
    def stop(self, request, project__uuid, uuid):
        task = self.get_object()
        task.stop()
        try:
            service = StartTaskService(task=task)
            service.execute()
        except CuncurrentTaskException:
            return response.Response()


