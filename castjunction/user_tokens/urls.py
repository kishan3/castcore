"""Urls for token management system."""
from django.conf.urls import include, url
from oscar_accounts.dashboard.app import application as accounts_app

from .views import (
    PaymentDetailsView,
    InviteView,
    PaymentInitialDataView,
    TokenView,
    web_payment,
    PaymentLandingView,
)

urlpatterns = [
    url(r"^dashboard/accounts/", include(accounts_app.urls)),
    url(r"^users/accounts/credits/", TokenView.as_view(), name="user_token_balance"),
    url(
        r"^users/(?P<pk>[0-9]+)/invite/",
        InviteView.as_view(),
        name="referral_url_invite",
    ),
    url(r"^tokens/order/", PaymentDetailsView.as_view(), name="token_order"),
    url(
        r"^payment/(?P<order_id>[0-9]+)/",
        PaymentInitialDataView.as_view(),
        name="api-payment",
    ),
    url(r"web-payment/", web_payment, name="web_payment"),
    url(r"landing-payment/", PaymentLandingView.as_view(), name="landing_payment"),
]
