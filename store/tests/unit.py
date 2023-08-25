import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from store.exceptions import *
from store.models import Agent, Order, Trip, DelayReport, Vendor


class AgentTestCase(TestCase):
    def setUp(self) -> None:
        self.agent_one = Agent.objects.create(user=User.objects.create(username="user1"))
        self.agent_two = Agent.objects.create(user=User.objects.create(username="user2"))

        vendor = Vendor.objects.create(name="vendor")
        self.order_one = Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() + datetime.timedelta(minutes=50),
            vendor=vendor,
        )
        self.order_two = Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() + datetime.timedelta(minutes=50),
            vendor=vendor,
        )
        self.report_one = DelayReport.objects.create(order=self.order_one)
        self.report_two = DelayReport.objects.create(order=self.order_two)

    def tearDown(self) -> None:
        DelayReport.objects.all().delete()

    def test_assign_report(self):
        self.assertFalse(self.agent_one.is_report_assigned)
        self.agent_one.assign_report()

        self.agent_one.refresh_from_db()
        self.report_one.refresh_from_db()
        self.report_two.refresh_from_db()

        self.assertTrue(self.agent_one.is_report_assigned)
        self.assertEqual(self.report_one.agent, self.agent_one)
        self.assertEqual(self.report_two.agent, None)

    def test_assign_report_twice(self):
        self.assertFalse(self.agent_one.is_report_assigned)
        self.agent_one.assign_report()

        with self.assertRaises(YouAlreadyHaveAnOrderToProcessException):
            self.agent_one.assign_report()

    def test_assign_report_two_agents(self):
        self.agent_one.assign_report()
        self.agent_two.assign_report()

        self.agent_one.refresh_from_db()
        self.report_one.refresh_from_db()
        self.assertTrue(self.agent_one.is_report_assigned)
        self.assertEqual(self.report_one.agent, self.agent_one)

        self.agent_two.refresh_from_db()
        self.report_two.refresh_from_db()
        self.assertTrue(self.agent_two.is_report_assigned)
        self.assertEqual(self.report_two.agent, self.agent_two)


class TripTestCase(TestCase):
    def setUp(self) -> None:
        vendor = Vendor.objects.create(name="vendor")
        self.order = Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() + datetime.timedelta(minutes=50),
            vendor=vendor,
        )
        self.trip = Trip.objects.create(
            order=self.order
        )

    def test_get_by_order(self):
        self.assertEqual(Trip.get_by_order(self.order), self.trip)


class OrderTestCase(TestCase):
    def setUp(self) -> None:
        vendor = Vendor.objects.create(name="vendor")

        self.not_reached_order = Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() + datetime.timedelta(minutes=50),
            vendor=vendor,
        )

        self.delayed_order = Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() - datetime.timedelta(minutes=1),
            vendor=vendor,
        )
        self.delayed_order_trip = Trip.objects.create(
            order=self.delayed_order
        )

        self.no_trip_order = Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() - datetime.timedelta(minutes=1),
            vendor=vendor,
        )

    def test_delay_not_reached(self):
        with self.assertRaises(DeliveryTimeNotReachedYetException):
            self.not_reached_order.delay()

    def test_delay(self):
        self.assertEqual(DelayReport.objects.count(), 0)
        self.delayed_order.delay()

        self.assertEqual(DelayReport.objects.count(), 1)
        report = DelayReport.objects.first()
        self.assertTrue(report.is_processed)
        self.assertEqual(report.order, self.delayed_order)
        self.assertEqual(report.agent, None)

        self.delayed_order.refresh_from_db()
        self.assertEqual(self.delayed_order.delivery_time, 65)

    def test_delay_twice(self):
        self.assertEqual(DelayReport.objects.count(), 0)
        self.no_trip_order.delay()
        self.assertEqual(DelayReport.objects.count(), 1)

        self.no_trip_order.delivery_time_datetime = datetime.datetime.now()
        self.no_trip_order.save()
        with self.assertRaises(YouAlreadyHaveRequestedException):
            self.no_trip_order.delay()
        self.assertEqual(DelayReport.objects.count(), 1)

    def test_delay_no_trip(self):
        self.assertEqual(DelayReport.objects.count(), 0)
        self.no_trip_order.delay()

        self.assertEqual(DelayReport.objects.count(), 1)
        report = DelayReport.objects.first()
        self.assertFalse(report.is_processed)
        self.assertEqual(report.order, self.no_trip_order)
        self.assertEqual(report.agent, None)

        self.no_trip_order.refresh_from_db()
        self.assertEqual(self.no_trip_order.delivery_time, 50)


class DeliveryTripTestCase(TestCase):

    def test_is_processing(self):
        vendor = Vendor.objects.create(name="vendor1")
        order = Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() - datetime.timedelta(minutes=50),
            vendor=vendor,
        )
        self.assertFalse(DelayReport.is_processing(order))
        order.delay()
        self.assertTrue(DelayReport.is_processing(order))

    def test_uniqueness(self):
        vendor = Vendor.objects.create(name="vendor1")
        order = Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() - datetime.timedelta(minutes=50),
            vendor=vendor,
        )
        DelayReport.create(
            order=order,
            is_processed=False
        )
        with self.assertRaises(DelayReportUniquenessError):
            DelayReport.create(
                order=order,
                is_processed=False
            )

    def test_get_report(self):
        vendor_one = Vendor.objects.create(name="vendor1")
        Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() - datetime.timedelta(minutes=50),
            vendor=vendor_one,
        ).delay()
        vendor_two = Vendor.objects.create(name="vendor2")
        Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() - datetime.timedelta(minutes=50),
            vendor=vendor_two,
        ).delay()
        Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() - datetime.timedelta(minutes=50),
            vendor=vendor_two,
        ).delay()
        report = DelayReport.get_report()
        self.assertEqual(report.count(), 2)
        self.assertEqual(report[0]["order__vendor__name"], vendor_two.name)
        self.assertEqual(report[0]["delay_count"], 2)
        self.assertEqual(report[1]["order__vendor__name"], vendor_one.name)
        self.assertEqual(report[1]["delay_count"], 1)
