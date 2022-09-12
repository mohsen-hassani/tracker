from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from apps.core.base import AbstractService
from .exceptions import InvalidActivationKey
from .models import User


class RegisterUserService(AbstractService):
    email = None
    password = None
    first_name = None
    last_name = None

    def execute(self):
        user = User.objects.create_user(
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name
        )
        self._send_activation_email(user)
        return user

    def _send_activation_email(self, user):
        subject = 'welcome to TrackerSoft'
        message = f'Hello {user.email}, thank you for using our app. Please follow this link to activate your account: {user.get_activation_url()}'
        email_from = settings.EMAIL_FROM
        recipient_list = [user.email, ]
        send_mail( subject, message, email_from, recipient_list )


class ActivateUserService(AbstractService):
    key = None

    def execute(self):
        try:
            user = User.objects.get(activation_key=self.key)
        except User.DoesNotExist as e:
            raise InvalidActivationKey() from e

        if (timezone.now() - user.created_at) > settings.USER_ACTIVATION_EXPIRATION:
            raise InvalidActivationKey()

        user.activate()
    