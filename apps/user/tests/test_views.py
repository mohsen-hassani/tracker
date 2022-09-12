from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.authtoken.views import ObtainAuthToken
from ..views import RegisterView
from ..models import User


COMMON_PASSWORD = 'P@ssw0rd'


class UserRegisterTests(APITestCase):
    def test_user_can_register_using_email_and_password(self):
        factory = APIRequestFactory()
        url = reverse('user:register')
        request = factory.post(url, {
            'email': 'dummy@mail.com',
            'password': f'{COMMON_PASSWORD}!@#',
            'first_name': 'Mohsen',
            'last_name': 'Hassani'
        })
        view = RegisterView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)

    def test_user_cant_register_with_poor_password(self):
        factory = APIRequestFactory()
        url = reverse('user:register')
        request = factory.post(url, {
            'email': 'dummy@mail.com',
            'password': 'P@ssw0rd',
            'first_name': 'Mohsen',
            'last_name': 'Hassani'
        })
        view = RegisterView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        error_code = response.data['password'][0].code
        self.assertEqual(error_code, 'password_too_common')


class UserLoginTests(APITestCase):
    def setUp(self):
        self.email = 'dummy@email.com'
        self.password = COMMON_PASSWORD

        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            first_name='Mohsen',
            last_name='Hassani'
        )

    def test_user_is_inactive_by_default(self):
        self.assertFalse(self.user.is_active)
        
    def test_inactive_user_cant_login(self):
        factory = APIRequestFactory()
        url = reverse('user:login')
        request = factory.post(url, {'username': self.email, 'password': self.password})
        view = ObtainAuthToken.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_active_user_can_login(self):
        self.user.activate()
        factory = APIRequestFactory()
        url = reverse('user:login')
        request = factory.post(url, {'username': self.email, 'password': self.password})
        view = ObtainAuthToken.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    
