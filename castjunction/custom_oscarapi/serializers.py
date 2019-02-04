"""Custom serializers for oscarapi."""
import warnings
from django.core.urlresolvers import reverse, NoReverseMatch

from rest_framework import serializers

from oscarapi import serializers as oscarapi_serializers
from oscar.core.loading import get_class, get_model

Selector = get_class('partner.strategy', 'Selector')
ShippingAddress = get_model('order', 'ShippingAddress')


class ProductSerializer(oscarapi_serializers.ProductSerializer):
    price = serializers.SerializerMethodField()

    def get_price(self, obj):
        request = self.context.get('request')
        strategy = Selector().strategy(request=request, user=request.user)
        ser = oscarapi_serializers.PriceSerializer(
            strategy.fetch_for_product(obj).price,
            context={'request': request})
        return ser.data


class OrderSerializer(oscarapi_serializers.OrderSerializer):

    def get_payment_url(self, obj):
        try:
            reverse('api-payment', args=(obj.pk,))
            return obj.pk
        except NoReverseMatch:
            msg = "You need to implement a view named 'api-payment' " \
                "which redirects to the payment provider and sets up the " \
                "callbacks."
            warnings.warn(msg)
            return msg


class CheckoutSerializer(oscarapi_serializers.CheckoutSerializer):

    def create(self, validated_data):
        try:
            basket = validated_data.get('basket')
            order_number = self.generate_order_number(basket)
            request = self.context['request']
            if validated_data.get('shipping_address'):
                shipping_address = ShippingAddress(
                    **validated_data['shipping_address'])
            else:
                shipping_address = None
            return self.place_order(
                order_number=order_number,
                user=request.user,
                basket=basket,
                shipping_address=shipping_address,
                shipping_method=validated_data.get('shipping_method'),
                shipping_charge=validated_data.get('shipping_charge'),
                billing_address=validated_data.get('billing_address'),
                order_total=validated_data.get('total'),
                guest_email=validated_data.get('guest_email') or ''
            )
        except ValueError as e:
            raise exceptions.NotAcceptable(e.message)
