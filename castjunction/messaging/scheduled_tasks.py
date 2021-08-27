"""Scheduled tasks."""
from datetime import datetime, timedelta


def broadcast_approved_jobs():
    """Test."""
    import django

    django.setup()
    import pytz
    from project.models import Job
    from users.models import Person
    from utils import choices
    from django.conf import settings as django_settings
    from .mails import JobApprovedEmailNotification

    # Fetch all approved jobs from 10 AM IST(i.e 4.30 UTC)
    # yesterday and  to 10 AM IST (i.e 4.30 UTC) today.
    broadcast_hour = 4
    broadcast_minute = 30
    broadcast_second = 0
    broadcast_microsecond = 0

    today = datetime.now(pytz.utc)
    today = today.replace(
        hour=broadcast_hour,
        minute=broadcast_minute,
        second=broadcast_second,
        microsecond=broadcast_microsecond,
    )
    yesterday = today - timedelta(days=1)

    all_jobs = Job.objects.filter(status="A", updated_at__range=(yesterday, today))
    all_users = Person.objects.filter(preference__email_notification=True)

    if all_jobs:
        for gender, _ in choices.GENDER_CHOICES:
            filtered_jobs = all_jobs.filter(
                required_gender__in=[gender, choices.NOT_SPECIFIED]
            )
            if filtered_jobs:
                filtered_users = list(
                    all_users.filter(gender=gender)
                    .exclude(email=None)
                    .values_list("email", flat=True)
                )
                context = {
                    "job_count": filtered_jobs.count(),
                    "jobs": filtered_jobs,
                    "domain": django_settings.DOMAIN,
                    "url": django_settings.JOB_OPPORTUNITIES_URL,
                }
                JobApprovedEmailNotification(
                    receiver=filtered_users, context=context
                ).send()
