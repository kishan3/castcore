"""Urls for user management of castjunction."""
from django.conf.urls import include, url

from .views import (
    UserViewSet,
    LoginView,
    FacebookLogin,
    TwitterLogin,
    GoogleLogin,
    UserLikeViewSet,
    ExperienceViewSet,
    EducationViewSet,
    BioViewSet,
    LanguageViewSet,
    SkillViewSet,
    InstituteViewSet,
    CitiesViewSet,
    CountriesViewSet,
    UserNotificationViewSet,
    PasswordResetView,
    PasswordResetConfirmView,
    ContactUsView,
    RegisterView,
    ScheduledInvitesViewSet,
    PersonViewSet,
    UserPreferenceView,
    UserEarningsView,
    ApplicationsOnJobsViewSet,
    VerificationActivitiesViewSet,
    VerifyEmailView,
    OTPPasswordResetConfirmView,
    CheckUserView,
    NotifyUserView,
)

from rest_framework_extensions.routers import ExtendedSimpleRouter as SimpleRouter
from project.views import UserJobsViewSet

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"experiences", ExperienceViewSet, base_name="user-experience")
router.register(r"educations", EducationViewSet, base_name="user-education")
# router.register(r'bio', BioViewSet, base_name='user-bio')
router.register(r"institutes", InstituteViewSet, base_name="user-bio")
router.register(
    r"notifications", UserNotificationViewSet, base_name="user_notifications"
)

simple_router = SimpleRouter()

(
    simple_router.register(r"users", UserViewSet).register(
        r"likes",
        UserLikeViewSet,
        "users-like",
        parents_query_lookups=["receiver_object_id"],
    )
)

urlpatterns = [
    url(r"users/likes/", UserLikeViewSet.as_view({"get": "get"}), name="likes"),
    url(r"contact/", ContactUsView.as_view({"post": "create"}), name="contact_us"),
    url(r"check-user/", CheckUserView.as_view({"post": "check"}), name="check_user"),
    url(r"notify-user/", NotifyUserView.as_view(), name="notify_user"),
    url(r"activate/", VerifyEmailView.as_view(), name="verify_email"),
    url(
        r"users/(?P<user_id>[0-9]+)/jobs/",
        UserJobsViewSet.as_view({"get": "list"}),
        name="user_jobs",
    ),
    url(
        r"users/scheduled_invites/",
        ScheduledInvitesViewSet.as_view({"get": "list"}),
        name="scheduled_invites",
    ),
    url(
        r"users/applications_on_my_jobs/",
        ApplicationsOnJobsViewSet.as_view({"get": "list"}),
        name="applications_on_myjobs",
    ),
    url(r"users/preferences/", UserPreferenceView.as_view(), name="user_prefernces"),
    url(r"users/earnings/", UserEarningsView.as_view(), name="user_earnings"),
    url(
        r"users/send_otp_sms",
        VerificationActivitiesViewSet.as_view({"post": "send_otp_sms"}),
        name="send_otp_sms",
    ),
    url(
        r"users/verify_phone/",
        VerificationActivitiesViewSet.as_view({"post": "verify_phone"}),
        name="verify_phone",
    ),
    url(r"^", include(simple_router.urls)),
    url(
        r"users/(?P<pk>[0-9]+)/bio/",
        BioViewSet.as_view({"patch": "update"}),
        name="update_bio",
    ),
    url(
        r"users/(?P<user_id>[0-9]+)/languages/",
        LanguageViewSet.as_view({"patch": "update"}),
        name="languages",
    ),
    url(
        r"users/(?P<user_id>[0-9]+)/skills/",
        SkillViewSet.as_view({"patch": "update"}),
        name="skills",
    ),
    url(r"users/(?P<user_id>[0-9]+)/", include(router.urls)),
    url(r"persons/", PersonViewSet.as_view({"get": "list"}), name="search_persons"),
    url(
        r"^languages/$", LanguageViewSet.as_view({"get": "list"}), name="languages_list"
    ),
    url(r"^skills/$", SkillViewSet.as_view({"get": "list"}), name="skills_list"),
    url(
        r"^institutes/$",
        InstituteViewSet.as_view({"get": "list"}),
        name="institutes_list",
    ),
    url(
        r"^experiences/$",
        ExperienceViewSet.as_view({"get": "list"}),
        name="experiences_list",
    ),
    url(
        r"^educations/$",
        EducationViewSet.as_view({"get": "list"}),
        name="educations_list",
    ),
    url(r"^cities/$", CitiesViewSet.as_view({"get": "list"}), name="cities_list"),
    url(r"^countries/$", CountriesViewSet.as_view({"get": "list"}), name="cities_list"),
    url(r"^bios/$", BioViewSet.as_view({"get": "list"}), name="bio_list"),
    url(r"^rest-auth/registration/", RegisterView.as_view(), name="rest_register"),
    url(r"^rest-auth/login/$", LoginView.as_view(), name="rest_login"),
    url(r"^rest-auth/facebook/$", FacebookLogin.as_view(), name="fb_login"),
    url(r"^rest-auth/twitter/$", TwitterLogin.as_view(), name="twitter_login"),
    url(r"^rest-auth/google/$", GoogleLogin.as_view(), name="google_login"),
    url(
        r"^rest-auth/password/reset/$",
        PasswordResetView.as_view(),
        name="password_reset",
    ),
    url(
        r"^rest-auth/password/reset/confirm/$",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    url(
        r"^rest-auth/password/reset/confirm_otp/$",
        OTPPasswordResetConfirmView.as_view(),
        name="otp_password_reset_confirm",
    ),
    url(r"^rest-auth/registration/", include("rest_auth.registration.urls")),
    url(r"^rest-auth/", include("rest_auth.urls")),
]
