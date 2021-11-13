from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework_recursive.fields import RecursiveField

from account.serializer import UserCommentSerializer
from courses.models.order import *

from courses.models.course import *
from courses.util import util_course
from extensions.utils import jalali_converter

User = get_user_model()


class DiscountCodeValidationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=8, )


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ('id', 'code', 'percent', 'max_price')


class OrderSetSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    price_final = serializers.ReadOnlyField()
    course_id = serializers.IntegerField()
    discount_id = serializers.IntegerField(required=False)
    status = serializers.IntegerField(min_value=1, max_value=3)
    bank_code = serializers.CharField(max_length=20, required=False)

    def validate_bank_code(self, obj):
        try:
            order = Order.objects.get(bank_code=obj)
            raise serializers.ValidationError({
                'bank_code': 'bank_code is exist'
            })
        except Order.DoesNotExist:
            return obj

    def get_discount_price(self, discount: Discount, price):
        discount_price = (price * (discount.percent / 100))
        return discount.max_price if discount_price > discount.max_price else discount_price

    def to_representation(self, instance):
        instance = super().to_representation(instance)
        data = [("Id_order", instance["id"]), ("price_final", instance["price_final"])]
        return data

    @transaction.atomic
    def create(self, validated_data):
        discount_price = 0
        discount = None
        user = self.context['request'].user
        try:
            course = Course.objects.get(id=validated_data['course_id'])
            price = course.price
            if course.discount > 0:
                price = price - (price * (course.discount / 100))
        except Course.DoesNotExist:
            raise serializers.ValidationError({
                'course_id': 'Course with this id does not exist'
            })
        is_exit_order = Order.objects.filter(user=user, course=course, status__lt=3).exists()
        if is_exit_order:
            raise serializers.ValidationError({
                'order': 'Order with this course and user exist'
            })
        if validated_data.get('discount_id'):
            try:
                discount = Discount.objects.get(id=validated_data['discount_id'])
                is_valid_discount = util_course.is_valid_discount(discount, user)
                if is_valid_discount[0]:
                    discount_price = self.get_discount_price(discount, course.price)
                else:
                    raise serializers.ValidationError(is_valid_discount[1])
            except Discount.DoesNotExist:
                raise serializers.ValidationError({
                    'discount_id': 'Discount with this id does not exist'
                })
        price_final = price - discount_price
        status = 2 if price_final == 0 else 1
        order = Order(
            user=user,
            course=course,
            discount=discount,
            discount_price=discount_price,
            price=price,
            price_final=price_final,
            status=status,
        )
        order.save()
        if status == 2:
            course.user.add(user)
        return order

    def update(self, instance, validated_data):
        if validated_data['status'] == 2 and validated_data.get("bank_code", False):
            instance.status = validated_data.get("status", instance.status)
            instance.bank_code = validated_data.get("bank_code", instance.bank_code)
            instance.course.user.add(instance.user)
        else:
            instance.status = 3
        instance.save()
        return instance


class OrderSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', max_length=500)

    class Meta:
        model = Order
        fields = (
            "id", "price_final", "course_title", "discount_price", "data_time_created", "price", "price_final",
            "status",
            "bank_code",)

    def to_representation(self, instance):
        # instance.data_time_created = instance.data_time_created.strftime('%Y-%m-%d')
        instance.data_time_created = jalali_converter(instance.data_time_created)
        instance.status = util_course.status_order(int(instance.status))
        instance = super().to_representation(instance)
        return instance


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        # exclude = ["chapter", ]
        fields = ("title", "slug", "Time_required", "free")

    def to_representation(self, instance):
        instance.slug = instance.slug if self.context["has_permission"] or instance.free else None
        return super().to_representation(instance)


class ChapterSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(many=True, source="lesson_set")

    class Meta:
        model = Chapter
        fields = ["title", "number_of_lesson", "description",
                  "lesson"
                  ]


class RepetitiveQuestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepetitiveQuestions
        exclude = ("course", "id")

    def to_representation(self, instance):
        # print("re", instance)
        instance = instance if instance else None
        instance = super(RepetitiveQuestionsSerializer, self).to_representation(instance)
        return instance


class FilterCommentsSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        data = data.filter(is_active=True)
        return super(FilterCommentsSerializer, self).to_representation(data)


class CommentChildSerializer(serializers.ModelSerializer):
    user = UserCommentSerializer()
    replies = SerializerMethodField()

    class Meta:
        list_serializer_class = FilterCommentsSerializer
        model = Comment
        fields = ["user", "comment", "creat_time",
                  "replies"
                  ]


class CommentSerializer(serializers.ModelSerializer):
    user = UserCommentSerializer()
    replies = SerializerMethodField()

    class Meta:
        list_serializer_class = FilterCommentsSerializer
        model = Comment
        fields = ["user", "comment", "creat_time",
                  "replies"
                  ]
        # exclude = ("course", "id", "is_active")

    def get_replies(self, obj):
        data = obj.children()
        if data:
            return CommentSerializer(data, many=True).data
        else:
            return None

    def to_representation(self, instance):
        instance.creat_time = jalali_converter(instance.creat_time)
        instance = super(CommentSerializer, self).to_representation(instance)
        return instance


class CourseDetailSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True, )
    chapters = ChapterSerializer(many=True, source="chapter_set")
    repetitive_questions = RepetitiveQuestionsSerializer(many=True, source="repetitivequestions_set")
    image = serializers.SerializerMethodField()
    comments = SerializerMethodField()

    # url = serializers.URLField(source="build_absolute_uri")
    class Meta:
        model = Course
        fields = ["title", "about", "image", "teaser", "price", "discount", "number_of_chapter",
                  "number_of_lesson",
                  "teacher",
                  "chapters",
                  "repetitive_questions",
                  "comments"
                  ]

    def get_image(self, course):
        request = self.context.get('request')
        image_url = course.image.url
        return request.build_absolute_uri(image_url)

    def get_comments(self, obj):
        comment_qs = Comment.objects.filter(course=obj, parent=None)
        if comment_qs:
            return CommentSerializer(comment_qs, many=True).data
        else:
            return []

    def to_representation(self, instance):
        # # instance.chapters = instance.chapters if instance.chapters else None
        # instance.repetitive_questions = instance.repetitive_questions if instance.repetitive_questions else None
        instance = super(CourseDetailSerializer, self).to_representation(instance)

        return instance


class TeacherCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ("name", "slug")


class CourseListSerializer(serializers.ModelSerializer):
    teacher = TeacherCourseSerializer()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ("title", "slug", "image", "teacher", "price", "discount")

    def get_image(self, course):
        request = self.context.get('request')
        image_url = course.image.url
        return request.build_absolute_uri(image_url)


class LessonReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"
