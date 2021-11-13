from datetime import date

from django.contrib.auth import get_user_model

from courses.models import order
from courses.models.order import Discount, Order

User = get_user_model()


class util_course:
    @staticmethod
    def is_valid_discount(discount: Discount, user: User):
        order = Order.objects.filter(user=user, discount=discount, status=2).exists()
        now = date.today()
        # Check the use of discount code
        if order:
            return False, {'code': ['The discount code Used']}

        # Check the expire time code
        if discount.expire_time < now:
            return False, {'code': ['The discount code Expire time']}

        # Check the expire capacity code
        if discount.count_use <= discount.number_of_use_code:
            return False, {'code': ['The discount code Expire capacity']}

        return True, "ok"

    @staticmethod
    def status_order(status: int) -> str:

        status_dict = {
            1: "In proses",
            2: "Success",
            3: 'Fail'
        }
        return status_dict[status]
