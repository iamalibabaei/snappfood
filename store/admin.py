from django.contrib import admin

from store.models import Agent, Order, Trip, DelayReport, Vendor


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    pass


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    pass


@admin.register(DelayReport)
class DelayReportAdmin(admin.ModelAdmin):
    pass
