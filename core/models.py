from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db import models
from django.utils.safestring import mark_safe
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class UserManager(BaseUserManager):
    def create_user(self, username, email, name, phone, password=None):
        """
        Creates and saves a User with the given email, name, phone and password.
        """
        if not username:
            raise ValueError('Users must have an username')
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            name=name,
            phone=phone,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, name, phone, password=None):
        """
        Creates and saves a superuser with the given email, name, phone and password.
        """
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
            name=name,
            phone=phone,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name=('Email'),
        max_length=255,
        unique=True,
    )
    username = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    profile = models.ImageField(upload_to='profile', default= "profile/profile.jpg")
    device_token = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'name', 'phone']

    def __str__(self):
        return self.name

    def image_tag(self):
        return mark_safe('<img src="{}" width="140" height="140"/>'.format(self.profile.url))
    image_tag.short_description = 'Profile'
    image_tag.allow_tags = True


    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return self.is_admin

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'



class MessageModel(models.Model):
    """
    This class represents a chat message. It has a owner (user), timestamp and
    the message body.

    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='user',
                      related_name='from_user', db_index=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='recipient',
                           related_name='to_user', db_index=True)
    timestamp = models.DateTimeField('timestamp', auto_now_add=True, editable=False,
                              db_index=True)
    body = models.TextField('body')

    def __str__(self):
        return str(self.id)

    def characters(self):
        """
        Toy function to count body characters.
        :return: body's char number
        """
        return len(self.body)

    def notify_ws_clients(self):
        """
        Inform client there is a new message.
        """
        notification = {
            'type': 'recieve_group_message',
            'message': '{}'.format(self.id)
        }

        channel_layer = get_channel_layer()
        print("user.id {}".format(self.user.id))
        print("user.id {}".format(self.recipient.id))

        async_to_sync(channel_layer.group_send)("{}".format(self.user.id), notification)
        async_to_sync(channel_layer.group_send)("{}".format(self.recipient.id), notification)

    def save(self, *args, **kwargs):
        """
        Trims white spaces, saves the message and notifies the recipient via WS
        if the message is new.
        """
        new = self.id
        self.body = self.body.strip()  # Trimming whitespaces from the body
        super(MessageModel, self).save(*args, **kwargs)
        if new is None:
            self.notify_ws_clients()

    # Meta
    class Meta:
        app_label = 'core'
        verbose_name = 'message'
        verbose_name_plural = 'messages'
        ordering = ('-timestamp',)
