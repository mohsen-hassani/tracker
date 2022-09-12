from uuid import uuid4
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, UserManager
from apps.core.mixins import Activable, Timestampable


def generate_activation_key():
    return uuid4().hex

class CustomUserManager(UserManager, models.Manager):
    def create_superuser(self, email, username=None, password = ..., **extra_fields):
        return super().create_superuser(email, email, password, **extra_fields)

    def create_user(self, email, username=None, password = ..., **extra_fields):
        return super().create_user(email, email, password, is_active=False, **extra_fields)


class User(Timestampable, Activable, AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    activation_key = models.CharField(max_length=32, default=generate_activation_key, unique=True)
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if self.pk == None:
            self.username = self.email
        return super().save(*args, **kwargs)

    def get_activation_url(self):
        return reverse('user:activate_account', args=(self.activation_key, ))

    @property
    def display_name(self):
        return (
            ' '.join((self.first_name, self.last_name))
            if self.first_name and self.last_name
            else self.email
        )
