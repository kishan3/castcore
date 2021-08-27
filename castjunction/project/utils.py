"""Utilites for job."""
from application.models import State

states_for_popular_jobs = [
    State.APPLIED,
    State.SHORTLISTED,
    State.INVITED,
    State.INVITE_ACCEPTED,
    State.INVITE_REJECTED,
    State.AUDITION_DONE,
    State.ACCEPTED,
    State.REJECTED,
    State.ONHOLD,
    State.JOBCLOSED,
]
