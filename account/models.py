from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save
from django.dispatch import receiver

import random
import os
import re


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, is_staff=False, is_active=True, is_admin=False):
        if not phone:
            raise ValueError('users must have a phone number')
        if not password:
            raise ValueError('user must have a password')

        user_obj = self.model(
            phone=phone
        )
        user_obj.set_password(password)
        user_obj.staff = is_staff
        user_obj.admin = is_admin
        user_obj.active = is_active
        user_obj.save(using=self._db)
        return user_obj

    def create_staffuser(self, phone, password=None):
        user = self.create_user(
            phone,
            password=password,
            is_staff=True,

        )
        return user

    def create_superuser(self, phone, password=None):
        user = self.create_user(
            phone,
            password=password,
            is_staff=True,
            is_admin=True,
        )
        return user


class User(AbstractBaseUser):
    phone_regex = RegexValidator(regex=r'^(\+98|0098|98|0)?9\d{9}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 14 digits allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=17, unique=True)
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone

    def get_full_name(self):
        return self.phone

    def get_short_name(self):
        return self.phone

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, account):
        return True

    @property
    def is_staff(self):
        return self.staff

    @property
    def is_admin(self):
        return self.admin

    @property
    def is_active(self):
        return self.active


def upload_image_path_profile(instance, filename):
    new_filename = random.randint(1, 9996666666)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(new_filename=new_filename, ext=ext)
    return "profile/{final_filename}".format(
        final_filename=final_filename
    )


def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    return name, ext


def is_valid_iran_code(input):
    if not re.search(r'^\d{10}$', input): return False
    check = int(input[9])
    s = sum(int(input[x]) * (10 - x) for x in range(9)) % 11
    return check == s if s < 2 else check + s == 11


def validate_national_code(value):
    if not is_valid_iran_code(value):
        raise ValidationError(
            _('%(value)s is not validate national code'),
            params={'value': value},
        )


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    national_code = models.CharField(validators=[validate_national_code], null=True, blank=True,
                                     max_length=10, unique=True)
    image = models.ImageField(upload_to=upload_image_path_profile, default=None, null=True, blank=True)
    invite_code = models.CharField(max_length=10, unique=True, default=None, null=True, )
    inviter_code = models.CharField(max_length=10, default=None, null=True, blank=True)

    def __str__(self):
        return str(self.user)


@receiver(post_save, sender=User)
def user_created_receiver(sender, instance, created, *args, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance, invite_code="{0:x}".format(int(instance.phone)))


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.discount_code = "{0:x}".format(int(instance.phone))
    instance.profile.save()


class PhoneOTP(models.Model):
    phone_regex = RegexValidator(regex=r'(\+98|0098|98|0)?9\d{9}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 14 digits "
                                         "allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=14, unique=True)
    otp = models.CharField(max_length=9, blank=True, null=True)
    count = models.IntegerField(default=0, help_text='Number of otp sent')
    time_send = models.DateTimeField(auto_now=True)
    verified = models.BooleanField(default=False, help_text='phone number verified')
    forgot = models.BooleanField(default=False, help_text='forgot password')

    def __str__(self):
        return str(self.phone) + ' is sent ' + str(self.otp)
