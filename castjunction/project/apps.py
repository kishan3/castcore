"""apps.py for project app."""
from django.apps import AppConfig


class ProjectConfig(AppConfig):
    name = 'project'

    def ready(self):
        from actstream import registry
        from .signals import incentive_for_job_approved
        registry.register(self.get_model('Job'))

        import django_rq
        from messaging.scheduled_tasks import broadcast_approved_jobs

        scheduler = django_rq.get_scheduler("default")
        # Delete any existing jobs in the scheduler when the app starts up
        for job in scheduler.get_jobs():
            job.delete()
        scheduler.cron(
            cron_string="30 4 * * *",
            func=broadcast_approved_jobs,  # Function to be queued
            queue_name=scheduler.queue_name
        )
