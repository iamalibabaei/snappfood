from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.exceptions import APIException


class YouAlreadyHaveAnOrderToProcessException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'You have an unprocessed order.'


class DeliveryTimeNotReachedYetException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Delivery time not reached yet!'


class YouAlreadyHaveRequestedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'You Have an unprocessed request!'


class DelayReportUniquenessError(ValidationError):
    def __init__(self):
        super().__init__("Uniqueness Violates")
