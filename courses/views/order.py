from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from courses import permissions
from courses.serializers import *
from courses.util import util_course
from crypto.util import Util

util = Util()


class VerificationDiscountCode(APIView):
    """
        Verify Discount code
    """

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        serializer = DiscountCodeValidationSerializer(data=request.data)
        is_valid = serializer.is_valid(raise_exception=True)
        if is_valid:
            try:
                code = serializer.data['code']
                discount = Discount.objects.get(code__iexact=code)
                is_valid_discount = util_course.is_valid_discount(discount, request.user)
                if is_valid_discount[0]:
                    result = DiscountSerializer(discount).data
                    return util.response_generator("ok", 200, result)
                else:
                    return Response(is_valid_discount[1], status=status.HTTP_400_BAD_REQUEST)

            except Discount.DoesNotExist:
                return Response({
                    'code': ['The discount code entered is incorrect']
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            # return util.response_generator(serializer.errors, 404, [])


class SetOrder(APIView):
    """
    Set order
    """
    permission_classes = (permissions.IsOwner,)

    @csrf_exempt
    def post(self, request, *args, **kwargs):

        serializer = OrderSetSerializer(data=request.data,
                                        context={
                                            'request': request
                                        })
        is_valid = serializer.is_valid(raise_exception=True)
        if is_valid:
            order = serializer.save()
            order.discount.update_number_of_use_code() if order.discount else None
            return util.response_generator("ok", 200, serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @csrf_exempt
    def patch(self, request, pk=None, *args, **kwargs):
        try:
            if pk:
                instance = Order.objects.get(id=pk)
                if instance.status == 1:
                    self.check_object_permissions(request, instance)
                    serializer = OrderSetSerializer(instance, data=request.data, partial=True)
                    if serializer.is_valid(raise_exception=True):
                        order = serializer.save()
                        serializers_order = OrderSerializer(order)
                        if order.status == 3:
                            instance.discount.update_number_of_use_code() if instance.discount is not None else None
                        return util.response_generator("ok", 200, serializers_order.data)
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'Error': ['the order is Not Editable']
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'Error': ['set order id']
                }, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({
                'order': ['The order entered is incorrect']
            }, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({
                'Error': [str(e)]
            }, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({
                'Error': [str(e)]
            }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            try:
                order = Order.objects.get(id=pk)
                self.check_object_permissions(request, order)
                serializers_order = OrderSerializer(order)
                return util.response_generator("ok", 200, serializers_order.data)
            except Order.DoesNotExist:
                return Response({
                    'order': ['The order entered is incorrect']},
                    status=status.HTTP_400_BAD_REQUEST)
            except PermissionDenied as e:
                return Response({
                    'Error': [str(e)]
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            order = Order.objects.filter(user__exact=request.user).order_by('-data_time_created')
            if order:
                serializers_order = OrderSerializer(order, many=True)
                return util.response_generator("ok", 200, serializers_order.data)
            else:
                return Response({
                    'order': ['No orders found']},
                    status=status.HTTP_400_BAD_REQUEST)
