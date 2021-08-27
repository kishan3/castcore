from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from .views import ProductList, CheckoutView, ClearBasketView

urlpatterns = [
    url(r"^products/$", ProductList.as_view(), name="product-list"),
    url(r"^checkout/$", CheckoutView.as_view(), name="api-checkout"),
    url(r"^basket/clear/$", ClearBasketView.as_view(), name="clear-basket"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
