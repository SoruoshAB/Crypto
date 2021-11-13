from datetime import datetime, date

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from courses.models.course import Course

User = get_user_model()


class Discount(models.Model):
    code = models.CharField(max_length=8, unique=True)
    percent = models.SmallIntegerField(validators=[MaxValueValidator(100), MinValueValidator(1)])
    expire_time = models.DateField()
    count_use = models.PositiveSmallIntegerField()
    max_price = models.PositiveIntegerField()
    number_of_use_code = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.code

    def update_number_of_use_code(self):
        self.number_of_use_code = self.order_set.filter(status__lte=2).count()
        print("update number discount :", self.number_of_use_code)
        self.save()


def validate_discount(value):
    value = Discount.objects.get(id=value)
    now = date.today()
    if value.expire_time < now:
        raise ValidationError(
            _('%(value)s Expire time'),
            params={'value': value},
        )

    if (value.count_use - 1) < value.number_of_use_code:
        if not value.order_set:
            raise ValidationError(
                _('%(value)s Expire capacity'),
                params={'value': value},
            )


class Order(models.Model):
    EXPLAIN_CHOICES = [
        (1, 'In proses'),
        (2, 'Success'),
        (3, 'Fail'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, blank=True, null=True,
                                 validators=[validate_discount])
    discount_price = models.PositiveIntegerField(blank=True, null=True)
    data_time_created = models.DateTimeField(auto_now=True)
    price = models.PositiveIntegerField()
    price_final = models.PositiveIntegerField(blank=True)
    status = models.SmallIntegerField(choices=EXPLAIN_CHOICES, default=1)
    bank_code = models.CharField(max_length=200, null=True, blank=True, unique=True)

    def delete(self, using=None, keep_parents=False):
        if self.status == 2:
            self.course.user.remove(self.user)
        super(Order, self).delete(using, keep_parents)
        self.discount.update_number_of_use_code() if self.discount else None

    def __str__(self):
        return self.course.title
