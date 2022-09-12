from datetime import timedelta
from django.test import TestCase
from django.conf import settings
from ..services import ActivateUserService
from ..models import User
from ..exceptions import InvalidActivationKey


class ActivateUserServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='dummy@mail.com',
            password='P@ssw0rd'
        )

    def test_user_can_activate(self):
        self.assertFalse(self.user.is_active)
        service = ActivateUserService(key=self.user.activation_key)
        service.execute()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_wrong_key_raise_exception(self):
        self.assertFalse(self.user.is_active)
        service = ActivateUserService(key="WRONG_KEY")
        with self.assertRaises(InvalidActivationKey):
            service.execute()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_expired_key_raise_exception(self):
        self.assertFalse(self.user.is_active)
        self.user.created_at = self.user.created_at - (settings.USER_ACTIVATION_EXPIRATION + timedelta(minutes=1))
        self.user.save()
        service = ActivateUserService(key=self.user.activation_key)
        with self.assertRaises(InvalidActivationKey):
            service.execute()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_not_expired_key_activate_user(self):
        self.assertFalse(self.user.is_active)
        self.user.created_at = self.user.created_at - (settings.USER_ACTIVATION_EXPIRATION - timedelta(minutes=1))
        self.user.save()
        service = ActivateUserService(key=self.user.activation_key)
        service.execute()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

