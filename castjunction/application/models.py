"""Application tracking and maintenance models."""
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django_fsm import FSMField, transition, ConcurrentTransitionMixin
from django.utils.translation import ugettext_lazy as _

from project.models import Job
from users.models import User
from multimedia.models import Image, Video
from utils.mixins import TimeFieldsMixin, StatusFieldMixin, CommonFieldsMixin
from utils import choices


class State(models.Model):
    """States for application lifecycle."""

    INTIATED = "intiated"
    PIPELINED = "pipelined"
    IGNORED = "ignored"
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    INVITED = "invited"
    INVITE_ACCEPTED = "invite_accepted"
    INVITE_REJECTED = "invite_rejected"
    AUDITION_DONE = "audition_done"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ONHOLD = "on_hold"
    JOBCLOSED = "job_closed"

    CHOICES = (
        (INTIATED, "Initiated"),
        (PIPELINED, "Pipelined"),
        (IGNORED, "Ignored"),
        (APPLIED, "Applied"),
        (SHORTLISTED, "Shortlisted"),
        (INVITED, "Invited"),
        (INVITE_ACCEPTED, "Invite_accepted"),
        (INVITE_REJECTED, "Invite_rejected"),
        (AUDITION_DONE, "Audition_done"),
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
        (ONHOLD, "On_hold"),
        (JOBCLOSED, "Job_closed"),
    )


class Application(TimeFieldsMixin, ConcurrentTransitionMixin):
    """Application for the jobs by Persons."""

    related_name = "applications"
    related_query_name = "application"
    job = models.ForeignKey(
        Job, null=True, related_name=related_name, related_query_name=related_query_name
    )

    user = models.ForeignKey(
        User, related_name=related_name, related_query_name=related_query_name
    )

    state = FSMField(
        default=State.INTIATED,
        choices=State.CHOICES,
        db_index=True,
        protected=True,
        verbose_name="Application state.",
    )

    reason_for_rejection = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Reason why the application was rejected.",
    )

    images = GenericRelation(Image, related_query_name=related_query_name)
    videos = GenericRelation(Video, related_query_name=related_query_name)

    class Meta:
        """Meta options."""

        unique_together = ("job", "user")
        verbose_name = "Application"
        verbose_name_plural = "Applications"
        permissions = (("can_reject_candidate", "Can reject a candiate."),)

    @transition(
        field=state,
        source=[State.INTIATED, State.PIPELINED, State.IGNORED],
        target=State.APPLIED,
    )
    def applied(self):
        return

    @transition(field=state, source=State.INTIATED, target=State.PIPELINED)
    def pipelined(self):
        return

    @transition(field=state, source=State.INTIATED, target=State.IGNORED)
    def ignored(self):
        return

    @transition(
        field=state, source=[State.APPLIED, State.INTIATED], target=State.INVITED
    )
    def direct_invited(self):
        return

    @transition(field=state, source=State.SHORTLISTED, target=State.INVITED)
    def invited(self):
        return

    @transition(field=state, source=State.INVITED, target=State.INVITE_ACCEPTED)
    def invite_accepted(self):
        return

    @transition(field=state, source=State.INVITED, target=State.INVITE_REJECTED)
    def invite_rejected(self):
        return

    @transition(field=state, source=State.INVITE_REJECTED, target=State.REJECTED)
    def application_terminate(self):
        return

    @transition(field=state, source=State.INVITE_ACCEPTED, target=State.AUDITION_DONE)
    def audition_done(self):
        return

    @transition(
        field=state, source=[State.AUDITION_DONE, State.ONHOLD], target=State.ACCEPTED
    )
    def candidate_accepted(self):
        return

    @transition(
        field=state, source=[State.AUDITION_DONE, State.ONHOLD], target=State.REJECTED
    )
    def candidate_rejected(self):
        return

    @transition(field=state, source=State.AUDITION_DONE, target=State.ONHOLD)
    def candidate_on_hold(self):
        return

    @transition(
        field=state,
        source=[
            State.IGNORED,
            State.PIPELINED,
            State.INVITED,
            State.APPLIED,
            State.SHORTLISTED,
            State.INVITE_ACCEPTED,
            State.INVITE_REJECTED,
            State.ONHOLD,
            State.AUDITION_DONE,
        ],
        target=State.JOBCLOSED,
    )
    def job_closed(self):
        return

    @transition(
        field=state,
        source=[
            State.INTIATED,
            State.APPLIED,
            State.SHORTLISTED,
            State.INVITED,
            State.INVITE_ACCEPTED,
            State.AUDITION_DONE,
            State.ONHOLD,
        ],
        target=State.REJECTED,
        permission="application.can_reject_candidate",
    )
    def agent_rejected(self):
        return

    @transition(
        field=state,
        source=[State.INTIATED, State.APPLIED],
        target=State.SHORTLISTED,
        permission="application.can_reject_candidate",
    )
    def shortlisted(self):
        return


class MobileAppVersion(TimeFieldsMixin, StatusFieldMixin):
    version_code = models.IntegerField(default=1)
    app_type = models.CharField(
        max_length=255, choices=choices.APP_TYPE_CHOICES, default=choices.TALENT
    )
    is_required = models.BooleanField(default=False)
    url = models.URLField()
    message = models.TextField()

    class Meta:
        unique_together = ("version_code", "app_type")


class AuditionInvite(CommonFieldsMixin):
    """Audition Invite for applicant."""

    date = models.DateTimeField(
        null=True, blank=True, help_text=(_("Date of Audition/Interview."))
    )

    audition_type = models.CharField(
        max_length=50, null=True, blank=True, choices=choices.AUDITION_TYPE_CHOICES
    )

    location = models.TextField(
        null=True, blank=True, help_text=(_("Address location for audition."))
    )

    applications = models.ManyToManyField(
        Application,
        related_name="audition_invites",
        related_query_name="audition_invite",
    )

    message_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Message id for message sent along with invite.",
    )
