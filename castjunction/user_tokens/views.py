"""Views for payment related tasks."""

from datetime import datetime
from hashlib import md5

from django.conf import settings as django_settings
from django.shortcuts import render
from django.http import HttpResponse

from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.contrib.auth.decorators import login_required

from oscar_accounts.models import Account
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError as RestFrameworkValidationError, NotFound

from pinax.referrals.models import Referral
from oscar.apps.order.models import Order
from users.models import User
from utils.utils import create_referral, group_required
from users.utils import (is_user_casting_director,
                         get_user_incentive_plan,
                         get_incetive_amount)
from messaging.messages import REFERRAL_SUBJECT, REFERRAL_MESSAGE

from .accounts_manager import credit_tokens_for_user, credit_to_reimbursement_account
from .serializers import AccountSerializer

from oscar.apps.checkout import mixins
from oscar.apps.payment import models


class PaymentDetailsView(
        mixins.OrderPlacementMixin,
        generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        order = Order.objects.get(number=data['MerchantRefNo'])
        # Payment successful! Record payment source
        if data.get('ResponseCode') == '0':
            source_type, __ = models.SourceType.objects.get_or_create(
                name="EBSGateway")
            source = models.Source.objects.create(
                source_type=source_type,
                order=order,
                amount_allocated=data['Amount'],
                reference=data['MerchantRefNo'])

            self.add_payment_source(source)

            # Record payment event
            self.add_payment_event('pre-auth', data['Amount'])
            lines = order.lines.all()
            for line in lines:
                token = line.product.attribute_values.filter(attribute__name='allocate_tokens')[0].value_integer
                credit_tokens_for_user(order.user, token)
            order.basket.status = "Submitted"
            order.status = "Success"
            order.save()
            # incentives for casting agent
            user = order.user
            referralresponse = user.referralresponse_set.first()
            # sometimes user might not be referred by any user.
            if referralresponse:
                referrer_user = referralresponse.target
                # check if user was referred by casting_director
                casting_director = is_user_casting_director(referrer_user)
                if casting_director:
                    if (datetime.today().date() - user.date_joined.date()).days <= django_settings.CA_INCENTIVE_THRESHOLD:

                        incentive_plan = get_user_incentive_plan(referrer_user)
                        amount = get_incetive_amount(incentive_plan, "user_paid")
                        try:
                            credit_to_reimbursement_account(referrer_user,
                                                            amount,
                                                            merchant_reference="user_paid")
                            # TODO: send diff types notifications to CA here.
                            referralresponse.action = "CASTING_DIRECTOR_PAID"
                            referralresponse.save()
                        except Exception as e:
                            raise e
            return HttpResponse("Payment success.")
        order.status = "Failed"
        return HttpResponse("Payment Failed.")


class InviteView(generics.ListCreateAPIView):
    """Invite users to join stageroute."""

    permission_classes = (IsAuthenticated,)

    def _generate_referral_link(self, user):
        try:
            referral_code = Referral.objects.get(user=user).code
        except Referral.DoesNotExist:
            referral_code = create_referral(user)

        return "{0}&{1}".format(
            django_settings.APP_URL,
            django_settings.INVITE_URL.format(
                **{"referral_code": referral_code}))

    def get(self, request, pk, *args, **kwargs):
        """Return referral url on invite."""
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            raise NotFound("user with user id {0} does not exist.".format(pk))
        referral_link = self._generate_referral_link(user)
        subject = REFERRAL_SUBJECT
        message = REFERRAL_MESSAGE.format(**{"url": referral_link})
        result = {
            "subject": subject,
            "message": message,
            "url": referral_link
        }
        return Response({"results": result})


class PaymentInitialDataView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):

        try:
            order = Order.objects.get(pk=kwargs.get('order_id'))
        except Order.DoesNotExist:
            raise NotFound("Order with id {} does not exists.".format(kwargs.get('order_id')))
        if order.user != request.user:
            raise RestFrameworkValidationError("You do not have permission to pay for this order.")
        result = {}
        if not order.shipping_address:
            city = django_settings.EBS_DEFAULT_CITY
            address = django_settings.EBS_DEFAULT_ADDRESS
            state = django_settings.EBS_DEFAULT_STATE
            postal_code = django_settings.EBS_DEFAULT_POSTALCODE
            country = django_settings.EBS_DEFAULT_COUNTRY
        else:
            city = order.shipping_address.city
            address = order.shipping_address.line1
            state = order.shipping_address.state
            postal_code = order.shipping_address.postcode
            country = order.shipping_address.country.iso_3166_1_a3.upper()
        if not order.user.phone:
            phone = django_settings.EBS_DEFAULT_PHONE
        else:
            phone = order.user.phone
        if not order.user.email:
            email = django_settings.EBS_DEFAULT_EMAIL
        else:
            email = order.user.email
        result.update({
            'account_id': django_settings.EBS_ACCOUNT_ID,
            'channel': django_settings.EBS_CHANNEL,
            'mode': django_settings.EBS_MODE,
            'currency': django_settings.EBS_CURRENCY,
            "page_id": django_settings.EBS_PAGE_ID,
            'city': city,
            "reference_no": order.number,
            "description": order.lines.last().description,
            "name": order.user.first_name,
            "address": address,
            "state": state,
            "postal_code": postal_code,
            'country': country,
            "phone": phone,
            "email": email,
            "return_url": django_settings.EBS_RETURN_URL,
        })
        result['amount'] = order.basket_total_incl_tax
        # calculate hash here.
        hash_string = django_settings.EBS_SECRET_KEY
        keys = sorted(list(result.keys()))

        for key in keys:
            hash_string += "|" + str(result[key])

        secure_hash = md5(hash_string.encode('utf-8')).hexdigest().upper()
        result['secure_hash'] = secure_hash
        return Response(result)


class TokenView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AccountSerializer

    def get(self, request, *args, **kwargs):
        try:
            token_account = Account.objects.get(account_type__name=django_settings.TOKEN_ACCOUNT,
                                                primary_user=request.user)
            reimbursement_account = Account.objects.get(
                account_type__name=django_settings.REIMBURSEMENT_ACCOUNT,
                primary_user=request.user)

        except Account.DoesNotExist:
            raise NotFound("User's token or reimbursement account does not exists.")

        return Response({
            "results": [self.get_serializer(token_account).data,
                        self.get_serializer(reimbursement_account).data
                        ]
        })


def web_payment(request):
    """Payment UI for agents."""
    context = {"token": request.user.auth_token.key}
    return render(request, "payment/payment.html", context=context)


class PaymentLandingView(View):

    @method_decorator(login_required(login_url='/admin/'))
    @method_decorator(group_required(['Support']))
    def get(self, request, *args, **kwargs):
        """Payment UI for agents."""
        context = {"token": request.user.auth_token.key}
        return render(request, "payment/landing_payment.html", context=context)
