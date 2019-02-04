"""Managers for accounts."""
import datetime
from django.conf import settings as django_settings
from oscar_accounts import models, facade

from oscar.core.loading import get_model

# from django.contrib.auth.models import User
# anonymous_account = models.Account.objects.create()

# date_limited_account = models.Account.objects.create(
#     start_date=today, end_date=next_week)

today = datetime.date.today()
next_year = today + datetime.timedelta(days=365)

Transfer = get_model('oscar_accounts', 'Transfer')


def create_no_limit_account(name):
    """Create system wide no credit limit account."""
    try:
        return models.Account.objects.create(
            credit_limit=None,
            name=name,
            start_date=today,
            end_date=next_year)
    except Exception as e:
        raise e


def create_limited_credit_account(user, account_type):
    """Create credi limited account for user."""
    try:
        acc_typ, created = models.AccountType.objects.get_or_create(
            path=account_type,
            depth=1,
            name=account_type)
        account = models.Account.objects.create(
            credit_limit=django_settings.ACCOUNTS_MAX_ACCOUNT_VALUE,
            primary_user=user,
            start_date=today,
            end_date=next_year,
            account_type=acc_typ,
            name="user_id_{}_{}".format(user.id, account_type)
        )
        # an ugly hack because oscar account is not compatible with
        # django 1.9 and it does not credit initial balance specified
        # in settings.
        if acc_typ.name == django_settings.TOKEN_ACCOUNT:
            credit_tokens_for_user(user, 10)
        return account
    except Exception as e:
        raise e


def debit_tokens_from_user(user, amount):
    """Tranfer from user account to sink account."""
    # staff_member = User.objects.get(username="staff")
    no_credit_limit_account_sink = None
    try:
        no_credit_limit_account_sink = models.Account.objects.get(name="sink_2016_no_limit")
    except models.Account.DoesNotExist:
        no_credit_limit_account_sink = create_no_limit_account("sink_2016_no_limit")

    user_account = models.Account.objects.get(
        primary_user=user,
        account_type__name=django_settings.TOKEN_ACCOUNT)

    trans = facade.transfer(source=user_account,
                            destination=no_credit_limit_account_sink,
                            amount=amount,)

    return trans


def credit_tokens_for_user(user, amount):
    """Tranfer from system wide accoutn to user account.

    Ideally this wiil be called after payment success by user.
    """
    # staff_member = User.objects.get(username="staff")
    no_credit_limit_account_source = None
    try:
        no_credit_limit_account_source = models.Account.objects.get(name="source_2016_no_limit")
    except models.Account.DoesNotExist:
        no_credit_limit_account_source = create_no_limit_account("source_2016_no_limit")

    user_account = models.Account.objects.get(
        primary_user=user,
        account_type__name=django_settings.TOKEN_ACCOUNT)

    trans = facade.transfer(source=no_credit_limit_account_source,
                            destination=user_account,
                            amount=amount,)

    return trans


def credit_to_reimbursement_account(user, amount, merchant_reference=None):

    no_credit_limit_account_source = None
    try:
        no_credit_limit_account_source = models.Account.objects.get(
            name="source_2016_no_limit")
    except models.Account.DoesNotExist:
        no_credit_limit_account_source = create_no_limit_account("source_2016_no_limit")

    user_account = models.Account.objects.get(
        primary_user=user,
        account_type__name=django_settings.REIMBURSEMENT_ACCOUNT)
    if not Transfer.objects.filter(merchant_reference=merchant_reference).exists():
        trans = facade.transfer(source=no_credit_limit_account_source,
                                destination=user_account,
                                amount=amount,
                                merchant_reference=merchant_reference)

        return trans
