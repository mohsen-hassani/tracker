from django.urls import path, include
from rest_framework import routers
from .views import ProjectViewSet
from .views import TaskViewSet


app_name = 'project'


project_router = routers.DefaultRouter()
project_router.register('', ProjectViewSet, basename='project_apis')
# For nested urls, I used regex instead of the `alanjds/drf-nested-routers` library to minimize third-party libraries usage
project_router.register('(?P<project__uuid>[^/.]+)/tasks', TaskViewSet, basename='task_apis')


urlpatterns = [
    path('projects/', include(project_router.urls))
]
