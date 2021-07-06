from django.conf.urls import url
from django.urls import path, include
from .views import *
from rest_framework_simplejwt import views as jwt_views
from rest_framework import routers

router = routers.SimpleRouter()
# router.register('', UserViewSet, basename="users")
urlpatterns = [
    path('Validate/PhoneRegister', ValidatePhoneRegister.as_view()),
    path('Validate/optRegister', ValidateOtpRegister.as_view()),
    path('register', RegisterApi.as_view()),
    path('Validate/PhoneForgot', ValidatePhoneForgot.as_view()),
    path('Validate/optForgot', ValidateOTPForgot.as_view()),
    path('password/change', ForgetPasswordChange.as_view()),
    path('profile/', ProfileRetrieveUpdate.as_view()),
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
]
