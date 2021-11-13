from django.contrib import admin

from courses.models.course import *
from courses.models.order import *


class CourseAdmin(admin.ModelAdmin):
    readonly_fields = ('number_of_chapter', 'number_of_lesson')
    prepopulated_fields = {'slug': ('title',)}


class ChapterAdmin(admin.ModelAdmin):
    readonly_fields = ('number_of_lesson',)


class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter',)
    list_filter = ('chapter',)
    prepopulated_fields = {'slug': ('title',)}



class CommentAdmin(admin.ModelAdmin):
    list_display = ('short_comment', 'is_active', 'creat_time')
    list_filter = ('course',)


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'course', 'user', 'price_final')
    list_filter = ('data_time_created', 'status', "discount")


class TeacherAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Chapter, ChapterAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(RepetitiveQuestions)
admin.site.register(Order, OrderAdmin)
admin.site.register(Discount)
