from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from store.models import *
from django.urls import reverse


class AppTesting(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_assign(self):
        user = User.objects.create_user(username="user1", password="password1")
        agent = Agent.objects.create(user=user)
        vendor = Vendor.objects.create(name="vendor")
        order = Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() + datetime.timedelta(minutes=50),
            vendor=vendor,
        )
        report = DelayReport.objects.create(
            order=order
        )

        self.client.login(username=user.username, password="password1")
        self.assertFalse(agent.is_report_assigned)
        response = self.client.post(reverse('assign'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        agent.refresh_from_db()
        report.refresh_from_db()
        self.assertEqual(agent, report.agent)
        self.assertTrue(agent.is_report_assigned)

    def test_delay(self):
        vendor = Vendor.objects.create(name="vendor")
        order = Order.objects.create(
            delivery_time=50,
            delivery_time_datetime=datetime.datetime.now() - datetime.timedelta(minutes=50),
            vendor=vendor,
        )
        Trip.objects.create(
            order=order
        )
        self.assertEqual(DelayReport.objects.count(), 0)
        response = self.client.post(reverse('announce', kwargs={'order_uuid': order.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DelayReport.objects.count(), 1)

    def test_report(self):
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

        response = self.client.get(reverse('report'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        first_vendor = response.json()[0]
        self.assertEqual(first_vendor['vendor_name'], vendor_two.name)


