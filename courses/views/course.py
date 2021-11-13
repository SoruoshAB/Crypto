from collections import OrderedDict

from rest_framework import status, generics, mixins, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404, GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings

from rest_framework.views import APIView

from courses import permissions
from courses.models.course import Course, Lesson
from courses.permissions import *
from courses.serializers import *
from crypto.pagination import PaginationHandlerMixin
from crypto.util import Util

util = Util()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 30


class CustomOrderingFilter(OrderingFilter):

    def remove_invalid_fields(self, queryset, fields, view, request):
        valid_fields = [item[0] for item in self.get_valid_fields(queryset, view, {'request': request})]
        valid_fields.append('free')

        print("valid_fields", valid_fields)

        def term_valid(term):
            if term.startswith("-"):
                term = term[1:]
            return term in valid_fields

        return [term for term in fields if term_valid(term)]

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            return queryset.order_by(*ordering) if "free" not in ordering else queryset.filter(price=0).order_by(
                *ordering.remove("free"))
        return queryset


class GetCourse(viewsets.ReadOnlyModelViewSet):
    """
    order by -->
        \n 1. -price: From more to less price
        \n 2. price: From less to more price
        \n 3. -id: From new to old course
        \n 4. id: From old to new course
    """
    queryset = Course.objects.all()
    ordering_fields = ['price', 'discount', 'id']
    pagination_class = StandardResultsSetPagination
    filter_backends = (CustomOrderingFilter,)

    # serializer_class = CourseListSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        if self.action == 'list':
            return CourseListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"request": request,
                                                            "has_permission": instance.has_permission(request.user)})
        return util.response_generator("ok", 200, serializer.data)


class CourseReviewList(ListAPIView):
    ordering_fields = ['price', 'discount', 'id']
    pagination_class = StandardResultsSetPagination
    serializer_class = CourseListSerializer
    queryset = Course.objects.all()
    filter_backends = (CustomOrderingFilter,)


class LessonDetail(RetrieveAPIView):
    serializer_class = LessonReviewSerializer
    lookup_field = 'slug'
    queryset = Lesson.objects.all()
    permission_classes = (IsOwnerLesson,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        print(serializer.data[api_settings.URL_FIELD_NAME])
        return util.response_generator("ok", 200, serializer.data)
