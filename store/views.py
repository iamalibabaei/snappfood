from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import get_object_or_404

from store.models import Order, DelayReport
from store.serilizers import ReportSerializer


def announce_delay(request, order_uuid):
    if request.method == 'GET':
        raise MethodNotAllowed("GET")

    order = get_object_or_404(Order, id=order_uuid)
    delayed = order.delay()
    if delayed:
        return JsonResponse(data={"data": {"eta": Order.ADDING_DELAY}, "status": True}, status=status.HTTP_200_OK)
    return JsonResponse(data={}, status=status.HTTP_200_OK)


@login_required
def assign_delayed_order(request):
    if request.method == 'GET':
        raise MethodNotAllowed("GET")

    agent = request.user.agent
    agent.assign_report()
    return JsonResponse(data={"status": "assigned"}, status=status.HTTP_200_OK)


def delay_report(request):
    if request.method == 'POST':
        raise MethodNotAllowed("POST")

    report = DelayReport.get_report()
    serializer = ReportSerializer(data=list(report), many=True)
    serializer.is_valid(raise_exception=True)
    return JsonResponse(data=serializer.data, safe=False, status=status.HTTP_200_OK)
