"""Signal for jobs."""
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from field_history.models import FieldHistory
from users.utils import (
    is_user_casting_director,
    get_user_incentive_plan,
    get_incetive_amount,
)
from users.models import Person
from utils import choices
from user_tokens.accounts_manager import credit_to_reimbursement_account
from messaging.tasks import bulk_send_push_notification
from messaging.messages import JOB_APPROVED_MESSAGE

from .models import Job


@receiver(pre_save, sender=Job, dispatch_uid="project.job.pre_save")
def change_job_state(sender, instance, **kwargs):
    """If last status and current status of job are approved then change current state to pending_approval."""
    last_status = FieldHistory.objects.filter(
        field_name="status", object_id=instance.id
    ).last()
    if (
        last_status
        and last_status.field_value == choices.APPROVED
        and instance.status == choices.APPROVED
    ):
        instance.status = choices.PENDING_APPROVAL


@receiver(post_save, sender=Job, dispatch_uid="project.job.post_save")
def incentive_for_job_approved(sender, created, instance, **kwargs):
    """Assign credit to casting director when his/her posted job gets approved."""
    if instance.status == choices.APPROVED:
        job_creator = instance.created_by
        casting_director = is_user_casting_director(job_creator)
        if casting_director:
            incentive_plan = get_user_incentive_plan(job_creator)
            amount = get_incetive_amount(incentive_plan, "job_post")
            credit_to_reimbursement_account(
                job_creator,
                amount,
                merchant_reference="job_post_{}".format(instance.id),
            )
        # send push notification to users.
        gender = instance.required_gender
        if gender == choices.NOT_SPECIFIED:
            users = Person.objects.all()
        else:
            users = Person.objects.filter(
                gender__in=[gender, choices.NOT_SPECIFIED],
                preference__push_notification=True,
            )

        if instance.ages:
            lower_age = instance.ages.lower
            upper_age = instance.ages.upper

            birth_date_upper_limit = datetime.today() - relativedelta(
                years=int(lower_age)
            )
            birth_date_lower_limit = datetime.today() - relativedelta(
                years=int(upper_age)
            )
            users = users.filter(
                date_of_birth__gte=birth_date_lower_limit.date()
            ).filter(date_of_birth__lte=birth_date_upper_limit.date())

        extra_data = {"extra": {"data": json.dumps({"job_id": instance.id})}}

        bulk_send_push_notification(
            users,
            JOB_APPROVED_MESSAGE.format(**{"job_title": instance.title}),
            **extra_data
        )
