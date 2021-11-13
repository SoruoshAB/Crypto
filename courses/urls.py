from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from courses.views.course import *
from courses.views.order import *

urlpatterns = [
    path('VerifyDiscountCode', VerificationDiscountCode.as_view()),
    path('Order', SetOrder.as_view()),
    path('Order/<int:pk>', SetOrder.as_view()),
    # path('', GetCourse),

    # path('<int:pk>', GetCourse),
    # path('', CourseReviewList.as_view()),
    re_path(r'^lesson/(?P<slug>[-a-zA-Z0-9_]+)/$', LessonDetail.as_view()),
]

router = DefaultRouter()
router.register(r'', GetCourse, basename='user')
urlpatterns += router.urls
