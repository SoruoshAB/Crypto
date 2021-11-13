import datetime
import re
from django.utils import timezone

from django.core import exceptions
import django.contrib.auth.password_validation as validators
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_writable_nested import NestedUpdateMixin, UniqueFieldsMixin
from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer

from account.models import PhoneOTP, Profile
from account.soapAPI import soapapi

User = get_user_model()


def validator_phone(value):
    regex_phone = '(\+98|0098|98|0)?9\d{9}$'
    if not bool(re.search(regex_phone, value)):
        raise serializers.ValidationError(
            "Phone number must be entered in the format: '+999999999'. Up to 14 digits allowed.")


# Validate Phone Register Serializer
class ValidatePhoneRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("phone",)

    def validate(self, data):
        phone = data.get('phone')
        count = 0
        phone_otp = PhoneOTP.objects.filter(phone__iexact=phone).first()
        if phone_otp:
            count = phone_otp.count
            phone_otp.count = count + 1
        else:
            count = count + 1
            phone_otp = PhoneOTP.objects.create(
                phone=phone,
                count=count,
            )
        if count > 7:
            raise serializers.ValidationError({
                'Otp': 'Maximum otp limits reached. Kindly support our customer care or try with '
                       'different number '
            })
        otp = soapapi.send_otp(phone)
        if otp:
            otp = str(otp)
            phone_otp.otp = otp
            phone_otp.save()
        else:
            raise serializers.ValidationError({
                'Otp': "OTP sending error. Please try after some time."
            })

        return super(ValidatePhoneRegisterSerializer, self).validate(data)


# Validate Otp Register serializer
class ValidateOtpRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[validator_phone], required=True)
    otp = serializers.CharField(max_length=6, required=True)

    def validate(self, data):
        phone = data.get('phone')
        otp_sent = data.get('otp')

        old = PhoneOTP.objects.filter(phone__iexact=phone)
        if old.exists():
            old = old.first()
            otp = old.otp
            if str(otp) == str(otp_sent):
                expire_time = old.time_send + datetime.timedelta(minutes=3)
                if timezone.now() <= expire_time:
                    old.verified = True
                    old.save()
                    return super(ValidateOtpRegisterSerializer, self).validate(data)
                else:
                    raise serializers.ValidationError({
                        'OTP': 'OTP time is expire, please try again'
                    })
            else:
                raise serializers.ValidationError({
                    'OTP': 'OTP incorrect, please try again'
                })
        else:
            raise serializers.ValidationError({
                'Phone': 'Phone not recognised. Kindly request a new otp with this number'
            })


# Register serializer
class RegisterSerializer(serializers.ModelSerializer):
    inviter_code = serializers.CharField(max_length=10, required=False)

    class Meta:
        model = User
        fields = ('phone', 'password', 'inviter_code')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        global phone_otp
        global profile_inviter
        profile_inviter = None
        inviter_code = data.get('inviter_code')
        if inviter_code:
            profile_inviter = Profile.objects.filter(invite_code=inviter_code).first()
            if not profile_inviter:
                raise serializers.ValidationError({'Inviter Code': "inviter code not found"})
        phone_otp = PhoneOTP.objects.filter(phone__iexact=data.get('phone')).first()
        if not phone_otp:
            raise serializers.ValidationError({
                'Phone': 'Phone number not recognised. Kindly request a new otp with this number.'
            })
        else:
            if not phone_otp.verified:
                raise serializers.ValidationError({
                    'Phone': 'Your otp was not verified earlier.'
                })
        # here data has all the fields which have validated values
        # so we can create a User instance out of it
        user = User(phone=data.get('phone'), password=data.get('password'))

        # get the password from the data
        password = data.get('password')

        errors = dict()
        try:
            # validate the password and catch the exception
            validators.validate_password(password=password, user=User)

        # the exception raised here is different than serializers.ValidationError
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)
        return super(RegisterSerializer, self).validate(data)

    def create(self, validated_data):
        inviter_code = None
        if validated_data.get('inviter_code'):
            inviter_code = validated_data.pop('inviter_code')
        user = User.objects.create_user(**validated_data)
        if profile_inviter:
            print(validated_data)
        user.profile.inviter_code = inviter_code
        phone_otp.delete()
        return user


# Phone Forget serializer
class ValidatePhoneForgetSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[validator_phone], required=True)

    def validate(self, data):
        phone = data.get('phone')
        count = 0
        user = User.objects.filter(phone__iexact=phone)
        if user.exists():
            phone_otp = PhoneOTP.objects.filter(phone__iexact=phone)
            if phone_otp.exists():
                phone_otp = phone_otp.first()
                count = phone_otp.count
                if count > 7:
                    raise serializers.ValidationError({
                        'OTP': 'Maximum otp limits reached. Kindly support our customer care or try with '
                               'different number or contact help centre.'
                    })
                phone_otp.count = count + 1
                phone_otp.forgot = True
                phone_otp.verified = False
            else:
                count = count + 1
                phone_otp = PhoneOTP.objects.create(
                    phone=phone,
                    count=count,
                    forgot=True
                )
            otp = soapapi.send_otp(phone)
            if otp:
                otp = str(otp)
                phone_otp.otp = otp
                phone_otp.save()
            else:
                raise serializers.ValidationError({
                    'OTP': "OTP sending error. Please try after some time."
                })
            return super(ValidatePhoneForgetSerializer, self).validate(data)
        else:
            raise serializers.ValidationError({
                'Phone': "user with this phone doesn't exists"
            })


# Validate Otp Forgot Serializer
class ValidateOtpForgotSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[validator_phone], required=True)
    otp = serializers.CharField(max_length=6, required=True)

    def validate(self, data):
        phone = data.get('phone')
        otp_sent = data.get('otp')
        old = PhoneOTP.objects.filter(phone__iexact=phone)
        if old.exists():
            old = old.first()
            if old.forgot == False:
                raise serializers.ValidationError({
                    'OTP': "This phone haven't send valid otp for forgot password. Request a new otp or "
                           "contact help centre. "
                })
            otp = old.otp
            if str(otp) == str(otp_sent):
                expire_time = old.time_send + datetime.timedelta(minutes=3)
                if timezone.now() <= expire_time:
                    old.verified = True
                    old.save()
                    return super(ValidateOtpForgotSerializer, self).validate(data)
                else:
                    raise serializers.ValidationError({
                        'OTP': 'OTP time was expire, please try again'
                    })
            else:
                raise serializers.ValidationError({
                    'OTP': 'OTP incorrect, please try again'
                })
        else:
            raise serializers.ValidationError({
                'Phone': 'Phone not recognised. Kindly request a new otp with this number'
            })


# Forget Password serializer
class ForgetPasswordSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(validators=[validator_phone], required=True)

    class Meta:
        model = User
        fields = ('password', 'phone')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        # get the password from the data
        password = data.get('password')
        phone = data.get('phone')

        # user = get_object_or_404(User, phone__iexact=data.get('phone'))

        errors = dict()
        try:
            # validate the password and catch the exception
            validators.validate_password(password=password, user=User)

        # the exception raised here is different than serializers.ValidationError
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)
        user = User.objects.filter(phone__iexact=phone)
        if user.exists():
            old = PhoneOTP.objects.filter(phone__iexact=phone)
            if old.exists():
                old = old.first()
                if old.forgot and old.verified:
                    user_obj = get_object_or_404(User, phone__iexact=phone)
                    if user_obj:
                        user_obj.set_password(password)
                        user_obj.active = True
                        user_obj.save()
                        old.delete()
                        return super(ForgetPasswordSerializer, self).validate(data)
                else:
                    raise serializers.ValidationError({
                        'OTP': 'OTP Verification failed. Please try again in previous step'
                    })
            else:
                raise serializers.ValidationError({
                    'Phone': 'Phone and otp are not matching or a new phone has entered. Request a new otp in '
                             'forgot password '
                })
        else:
            raise serializers.ValidationError({
                'Phone': "user with this phone doesn't exists"
            })


class UserSerializer(serializers.ModelSerializer):
    # profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ("id", "phone", "name",)
        read_only_fields = ("phone", "id")


class ProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="user.phone", read_only=True)
    name = serializers.CharField(required=True)

    class Meta:
        model = Profile
        fields = ('email', 'image', 'national_code', 'name', 'phone',)


class SetInviterCodeSerializer(serializers.ModelSerializer):
    inviter_code = serializers.CharField(max_length=10)

    class Mate:
        model = User
        fields = ('profile', 'inviter_code')

    def validate(self, data):
        inviter_code = data.get("inviter_code")


class UserCommentSerializer(serializers.ModelSerializer):
    phone = serializers.CharField()

    class Meta:
        model = Profile
        fields = (
            # 'image',
            # 'name',
            'phone',
        )

    def to_representation(self, instance):
        instance.phone = re.sub(r".*?(\d{4})(\d{3})(\d{3})$", r'0\1***\3', instance.phone)
        instance = super().to_representation(instance)
        return instance
