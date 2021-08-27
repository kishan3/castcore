"""Utility for applications."""

from django.conf import settings as django_settings
from rest_framework.exceptions import ValidationError
from oscar_accounts import models
from user_tokens.accounts_manager import create_limited_credit_account
from utils.utils import check_person_information


def checks_before_apply(user, job):
    """Check person info and user's remaining token balance."""
    result = check_person_information(user.person)
    if False in result.values():
        raise ValidationError(result)
    try:
        token_account = models.AccountType.objects.get(
            name=django_settings.TOKEN_ACCOUNT
        )
        user_token_account = models.Account.objects.get(
            primary_user=user, account_type=token_account
        )
    except models.Account.DoesNotExist:
        reimbursement_acc = models.AccountType.objects.get(
            name=django_settings.REIMBURSEMENT_ACCOUNT
        )
        user_token_account = create_limited_credit_account(
            user=user, account_type=token_account
        )
        create_limited_credit_account(user=user, account_type=reimbursement_acc)

    if user_token_account.balance < job.required_tokens:
        raise ValidationError(
            {"credit": "You don't have enough tokens to apply to this job."}
        )
    return True
