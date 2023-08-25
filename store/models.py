from __future__ import annotations
import datetime
import uuid

from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Count, QuerySet

from store.exceptions import YouAlreadyHaveAnOrderToProcessException, DeliveryTimeNotReachedYetException, \
    YouAlreadyHaveRequestedException, DelayReportUniquenessError


class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_report_assigned = models.BooleanField(default=False)

    def assign_report(self):
        if self.is_report_assigned:
            raise YouAlreadyHaveAnOrderToProcessException()

        with transaction.atomic():
            report = DelayReport.objects.filter(is_processed=False, agent__isnull=True).select_for_update().first()
            report.agent = self
            report.save()
            self.is_report_assigned = True
            self.save()


class Vendor(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Order(models.Model):
    ADDING_DELAY = 15

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now=True)
    delivery_time = models.IntegerField()
    delivery_time_datetime = models.DateTimeField()

    def delay(self) -> bool:
        if self.delivery_time_datetime >= datetime.datetime.now():
            raise DeliveryTimeNotReachedYetException()

        if DelayReport.is_processing(self):
            raise YouAlreadyHaveRequestedException()

        with transaction.atomic():
            try:
                trip = Trip.get_by_order(self)
            except Trip.DoesNotExist:
                self._add_delay_report(False)
                return False
            if trip.status in Trip.Status.DELAY_STATUSES:
                self._add_delay_report(True)
                self.delivery_time_datetime = datetime.datetime.now() + datetime.timedelta(minutes=self.ADDING_DELAY)
                self.delivery_time += self.ADDING_DELAY
                self.save()
                return True
            else:
                self._add_delay_report(False)
                return False

    def _add_delay_report(self, is_processed: bool = False):
        try:
            DelayReport.create(self, is_processed)
        except DelayReportUniquenessError:
            raise YouAlreadyHaveRequestedException()


class Trip(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "ASSIGNED"
        AT_VENDOR = "at_vendor", "AT_VENDOR"
        PICKED = "picked", "PICKED"
        DELIVERED = "delivered", "DELIVERED"

        DELAY_STATUSES = [ASSIGNED, AT_VENDOR, PICKED]

    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, choices=Status.choices, default=Status.ASSIGNED)

    # driver = models.ForeignKey(Driver, on_delete=models.CASCADE) probably in a complete project we need this

    @classmethod
    def get_by_order(cls, order: Order) -> 'Trip':
        return cls.objects.get(order=order)


class DelayReport(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)

    @classmethod
    def is_processing(cls, order: Order) -> bool:
        return cls.objects.filter(is_processed=False, order=order).count() > 0

    @classmethod
    def create(cls, order: Order, is_processed: bool):
        cls.objects.create(
            order=order,
            is_processed=is_processed,
        )

    @classmethod
    def get_report(cls) -> QuerySet:
        past_week = datetime.datetime.now() - datetime.timedelta(days=7)
        return DelayReport.objects.filter(
            created_at__gte=past_week
        ).values(
            'order__vendor'
        ).annotate(
            delay_count=Count('id')
        ).values('order__vendor__name', 'delay_count').order_by('-delay_count')

    def clean_unique(self):
        if self.is_processing(self.order):
            raise DelayReportUniquenessError()

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.clean_unique()
        return super().save(*args, **kwargs)
