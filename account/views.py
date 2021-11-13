from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializer import *


# Validate Phone for Register user
class ValidatePhoneRegister(APIView):
    """
    This class view takes phone number and if it doesn't exists already then it sends otp for
    first coming phone numbers
    """
    permission_classes = [permissions.AllowAny, ]

    def post(self, request, *args, **kwargs):
        serializer = ValidatePhoneRegisterSerializer(data=request.data)
        is_valid = serializer.is_valid(raise_exception=True)
        if is_valid:
            return Response({
                'message': 'Otp has been sent successfully.'
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Validate Otp for Register user
class ValidateOtpRegister(APIView):
    """
    If you have received otp, post a request with phone and that otp and you will be redirected to set the password

    """
    permission_classes = [permissions.AllowAny, ]

    def post(self, request, *args, **kwargs):
        serializer = ValidateOtpRegisterSerializer(data=request.data)
        is_valid = serializer.is_valid(raise_exception=True)
        if is_valid:
            return Response({
                'message': 'OTP matched, phone number is verified'
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Register API
class RegisterApi(APIView):
    """
        This class view takes phone number and password, set a new user
    """
    permission_classes = [permissions.AllowAny, ]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            user.save()
            token_serializer = TokenObtainPairSerializer(data=request.data)
            if token_serializer.is_valid(raise_exception=True):
                token = token_serializer.validated_data
                return Response({"data": token, })
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Validate Phone for Forgot Password
class ValidatePhoneForgot(APIView):
    """
    Validate if account is there for a given phone number and then send otp for forgot password reset
    """
    permission_classes = [permissions.AllowAny, ]

    def post(self, request, *args, **kwargs):
        serializer = ValidatePhoneForgetSerializer(data=request.data)
        is_valid = serializer.is_valid(raise_exception=True)
        if is_valid:
            return Response({'OTP': 'OTP has been sent for password reset'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Validate Otp for Forgot Password
class ValidateOTPForgot(APIView):
    """
    If you have received an otp, post a request with phone and that otp and you will be redirected to reset the
    forgotted password
    """
    permission_classes = [permissions.AllowAny, ]

    def post(self, request, *args, **kwargs):
        serializer = ValidateOtpForgotSerializer(data=request.data)
        is_valid = serializer.is_valid(raise_exception=True)
        if is_valid:
            return Response({
                'message': 'OTP matched, kindly proceed to create new password'
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# set new password
class ForgetPasswordChange(APIView):
    """
    if forgot is valid and account exists then only pass otp, phone and password to reset the password. All
    three should match.
    """
    permission_classes = [permissions.AllowAny, ]

    def post(self, request, *args, **kwargs):
        serializer = ForgetPasswordSerializer(data=request.data)
        is_valid = serializer.is_valid(raise_exception=True)
        if is_valid:
            return Response({
                'message': 'Password changed successfully. Please Login'
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileRetrieveUpdate(generics.RetrieveUpdateAPIView):
    """
    take user from Authorization and get profile data , update data
    """
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile
