from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('apps.project.urls', namespace='project')),
    path('api/v1/accounts/', include('apps.user.urls', namespace='user')),
    path('admin/', admin.site.urls),
]
