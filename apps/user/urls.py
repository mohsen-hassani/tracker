from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import ActivateUser, ProfileView, RegisterView


app_name = 'user'


urlpatterns = [
    path('login/', obtain_auth_token, name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<key>/', ActivateUser.as_view(), name='activate_account'),
]