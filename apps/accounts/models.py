from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Value
from django.db.models.functions import Lower

from .validators import validate_ascii_email


class UserManager(BaseUserManager):
    def get_by_natural_key(self, username):
        # The same expression as the unique constraint on User, so this finds at
        # most one user. createsuperuser uses it to report an email as taken.
        return self.alias(email_lower=Lower('email')).get(
            email_lower=Lower(Value(username))
        )

    def _create_user(self, email, password, **extra_fields):
        if not (email or '').strip():
            raise ValueError('An email address is required.')
        # Before stripping, because strip() also removes non-ASCII whitespace.
        validate_ascii_email(email)
        user = self.model(email=email.strip(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields['is_staff'] is not True:
            raise ValueError('A superuser must have is_staff=True.')
        if extra_fields['is_superuser'] is not True:
            raise ValueError('A superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """A user who logs in with a unique email instead of a username (D8)."""

    username = None
    # Django requires USERNAME_FIELD to be unique on its own, so unique=True stays
    # alongside the case-insensitive constraint below.
    email = models.EmailField(
        'email address', unique=True, validators=[validate_ascii_email]
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(Lower('email'), name='accounts_user_email_ci_unique'),
            models.CheckConstraint(
                condition=~models.Q(email=''), name='accounts_user_email_not_empty'
            ),
        ]
