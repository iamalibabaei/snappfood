from rest_framework import serializers


class ReportSerializer(serializers.Serializer):
    vendor_name = serializers.CharField()
    count = serializers.IntegerField()

    def to_internal_value(self, data):
        data['vendor_name'] = data.get('order__vendor__name', None)
        data['count'] = data.get('delay_count', None)
        return data
