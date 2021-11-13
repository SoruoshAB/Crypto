from django.db import models
from django.contrib.auth import get_user_model
from django.template.defaultfilters import truncatechars
from django.core.validators import MaxValueValidator, MinValueValidator

User = get_user_model()


def host_url():
    return "http://example.com"


class Teacher(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(default=None, upload_to='T')
    description = models.TextField()

    def __str__(self):
        return self.name


class Course(models.Model):
    user = models.ManyToManyField(User, blank=True, )
    title = models.CharField(max_length=500)
    slug = models.SlugField(unique=True)
    about = models.TextField()
    image = models.ImageField(default=None, upload_to='U')
    teaser = models.CharField(max_length=500, help_text="write just name of link")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    price = models.IntegerField(default=0, )
    discount = models.SmallIntegerField(validators=[MaxValueValidator(100), MinValueValidator(0)], default=0)
    number_of_chapter = models.IntegerField(default=0)
    number_of_lesson = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.teaser = f'{host_url()}/teaser/{self.teaser}'
        super(Course, self).save(*args, **kwargs)

    def update_number_of_chapter(self):
        for course in Course.objects.all():
            course.number_of_chapter = course.chapter_set.count()
            course.save()

    def update_number_of_lesson(self):
        for course in Course.objects.all():
            number_of_lesson = course.chapter_set.aggregate(total_lesson=models.Sum('number_of_lesson'))
            course.number_of_lesson = number_of_lesson['total_lesson'] if number_of_lesson['total_lesson'] else 0
            course.save()

    def has_permission(self, user: User):
        return True if user in self.user.all() else False

    def __str__(self):
        return self.title


class Chapter(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    number_of_lesson = models.IntegerField(default=0)
    description = models.TextField()

    def update_number_of_lesson(self):
        self.number_of_lesson = self.lesson_set.count()
        self.save()
        self.course.update_number_of_lesson()

    def save(self, *args, **kwargs):
        super(Chapter, self).save(*args, **kwargs)
        self.course.update_number_of_chapter()
        self.course.update_number_of_lesson()

    def __str__(self):
        return self.title


class Lesson(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    slug = models.SlugField(unique=True)
    link_HQ = models.CharField(max_length=500, help_text="write just name of link")
    link_LQ = models.CharField(max_length=500, help_text="write just name of link")
    Time_required = models.SmallIntegerField()
    description = models.TextField(null=True)
    free = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.link_HQ = f'{host_url()}/link_HQ/{self.link_HQ}'
            self.link_LQ = f'{host_url()}/link_LQ/{self.link_LQ}'
        super(Lesson, self).save(*args, **kwargs)
        self.chapter.update_number_of_lesson()

    def __str__(self):
        return self.title


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    comment = models.TextField()
    parent = models.ForeignKey('self', related_name='child', null=True, blank=True, on_delete=models.CASCADE)
    creat_time = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    # object = CommentManger()

    def children(self):  # reply
        return Comment.objects.filter(parent=self)

    @property
    def is_parent(self):
        return True if self.parent is None else False

    @property
    def short_comment(self):
        return truncatechars(self.comment, 50)

    def __str__(self):
        return truncatechars(self.comment, 50)


class RepetitiveQuestions(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()

    def __str__(self):
        return truncatechars(self.question, 50)
