"""Custom views for oscarapi."""
from rest_framework import filters
from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework.response import Response

from oscarapi.views import basic, checkout
from oscar.core.loading import get_model
from oscarapi import serializers as oscarapi_serializers
from .serializers import ProductSerializer, CheckoutSerializer, OrderSerializer

Product = get_model('catalogue', 'Product')


class ProductList(basic.ProductList):
    queryset = Product.objects.all()
    permission_classes = (AllowAny,)
    # TODO: order products by price_incl_tax
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('stockrecords',)
    ordering = ('stockrecords__price_excl_tax')

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'GET':
            return ProductSerializer
        else:
            return oscarapi_serializers.ProductLinkSerializer


class CheckoutView(checkout.CheckoutView):
    serializer_class = CheckoutSerializer
    order_serializer_class = OrderSerializer


class ClearBasketView(generics.GenericAPIView):

    def post(self, request, *args, **kwargs):
        """Get user's basket and delete its lines."""
        basket = request.user.baskets.last()
        if basket:
            lines = basket.lines.all()
            if lines:
                try:
                    for line in lines:
                        line.delete()
                except Exception as e:
                    raise e
                return Response({"success": "Basket cleared successfully."})
        return Response({"success": "Basket is already empty."})
