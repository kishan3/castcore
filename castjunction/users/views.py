"""Views for user app."""
import ast
import random
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import django_filters
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings as django_settings
from django.db.models import Sum, Count

from allauth.account import app_settings as allauth_settings

from drf_haystack.viewsets import HaystackViewSet

from rest_auth.views import LoginView as BaseLoginView
from rest_auth.registration.views import (
    SocialLoginView as BaseSocialLoginView,
    RegisterView as BaseRegisterView,
)

from rest_framework import viewsets, mixins, generics, filters, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework_extensions.decorators import link

from pinax.likes.models import Like

from pinax.referrals.models import ReferralResponse

from cities.models import City, Country

from oscar_accounts.models import Transaction
from notifications.serializers import ActionSerializer
from notifications.models import Action
from messaging.mails import ResetPasswordEmailNotification, NotifyUser
from messaging.tasks import send_mail, send_sms
from messaging.messages import OTP_SMS, RESET_PASSWORD_OTP_SMS

from application.models import State, Application
from application.serializers import ApplicationSerializer, ApplicationDetailSerializer
from project.serializers import JobSerializer
from project.models import Job
from utils import choices
from utils.utils import last_day_of_month, string_to_date

from .models import (
    User,
    Person,
    Experience,
    Education,
    Institute,
    Bio,
    Language,
    Skill,
    SearchableField,
    UserPreference,
)
from .utils import (
    is_user_casting_director,
    get_email_context,
    PERCENTAGE_BASIC_DETAILS_FIELDS,
    update_users_profile_percentage,
    increase_percentage,
)
from .permissions import IsOwnerOrReadOnly, IsCastingDirector, IsSupportGroupMember

from .adapters import (
    FacebookOAuth2AdapterFixed,
    TwitterOAuth2AdapterFixed,
    GoogleOAuth2AdapterFixed,
)
from .serializers import (
    UserSerializer,
    CustomSocialLoginSerializer,
    TwitterLoginSerializer,
    LikeSerializer,
    PersonSerializer,
    CompanySerializer,
    ExperienceSerializer,
    EducationSerializer,
    BioSerializer,
    LanguageSerializer,
    SkillSerializer,
    InstituteSerializer,
    CitySerializer,
    CountrySerializer,
    EducationSearchSerializer,
    ExperienceSearchSerializer,
    SearchableFieldSerializer,
    PasswordResetConfirmSerializer,
    ReferralResponseSerializer,
    TokenSerializer,
    UidSerializer,
    UserPreferenceSerializer,
    PersonPartialSerializer,
    OTPPasswordResetConfirmSerializer,
)

from haystack.query import SearchQuerySet


class RegisterView(BaseRegisterView):
    def get_response_data(self, user):
        if (
            allauth_settings.EMAIL_VERIFICATION
            == allauth_settings.EmailVerificationMethod.MANDATORY
        ):
            return {}

        return TokenSerializer(user.auth_token, context={"request": self.request}).data


class LoginView(BaseLoginView):
    def get_response(self):
        return Response(
            self.response_serializer(
                self.token, context={"request": self.request}
            ).data,
            status=status.HTTP_200_OK,
        )


class SocialLoginView(BaseSocialLoginView, LoginView):
    pass


class FacebookSocialLoginView(SocialLoginView):
    """FB social login view."""

    serializer_class = CustomSocialLoginSerializer


class FacebookLogin(FacebookSocialLoginView):
    """Facebook login view."""

    adapter_class = FacebookOAuth2AdapterFixed


class TwitterLogin(LoginView):
    """Twitter login view."""

    serializer_class = TwitterLoginSerializer
    adapter_class = TwitterOAuth2AdapterFixed


class GoogleLogin(SocialLoginView):
    """Google login view."""

    adapter_class = GoogleOAuth2AdapterFixed
    serializer_class = CustomSocialLoginSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Create, Updates, and retrives User accounts."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (
        IsOwnerOrReadOnly,
        IsAuthenticated,
    )

    def _get_object(self):
        instance = self.get_object()
        if instance.user_type == User.PERSON:
            instance = instance.person
        else:
            instance = instance.company
        return instance

    def get_serializer_class(self):
        if self.action == "list":
            return super().get_serializer_class()
        else:
            if self.request.user.user_type == User.PERSON:
                if self.request.user.id != int(self.kwargs.get("pk")):
                    return PersonPartialSerializer
                return PersonSerializer
            elif self.request.user.user_type == User.COMPANY:
                return CompanySerializer

    def retrieve(self, request, *args, **kwargs):
        """retrieve."""
        instance = self._get_object()
        serializer = self.get_serializer(instance)
        # user = self.get_object()
        # # send notifications if casting director viewed other person's profile.
        # if request.user.id != instance.id and is_user_casting_director(request.user):
        #     send_push_notification(user, PROFILE_VIEWED)
        #     if user.preferences.email_notification:
        #         context = {"first_name": instance.first_name}
        #         ProfileViewedEmailNotification(
        #             instance.email,
        #             context=context).send()
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """update."""
        instance = self._get_object()
        data = request.data.copy()
        percentage = getattr(instance, "profile_completion_percentage")
        for key in request.data.keys():
            if key in PERCENTAGE_BASIC_DETAILS_FIELDS.keys() and getattr(
                instance, key
            ) in ["NS", None]:
                percentage += PERCENTAGE_BASIC_DETAILS_FIELDS[key]

        data.update({"profile_completion_percentage": percentage})

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(serializer.data)

    @link(permission_classes=[IsAuthenticated], is_for_list=True)
    def referral_responses(self, request):
        """Return referral response of users referred."""
        referred_users = ReferralResponse.objects.filter(
            referral__in=request.user.referral_codes.all()
        )

        action = request.GET.get("action")
        if action == "paid_users":
            referred_users = referred_users.filter(action="CASTING_DIRECTOR_PAID")
        page = self.paginate_queryset(referred_users)
        if page is not None:
            serializer = ReferralResponseSerializer(
                page, many=True, context={"request": self.request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = ReferralResponseSerializer(
            referred_users, many=True, context={"request": self.request}
        )
        return Response(serializer.data)

    @link(permission_classes=[IsAuthenticated], is_for_list=True)
    def sales(self, request):
        """Return counts of users, packages bought and earnings."""
        result = {"referred_users_count": 0, "products_bought": 0, "total_earnings": 0}
        referred_users = ReferralResponse.objects.filter(
            referral__in=request.user.referral_codes.all()
        )
        result["referred_users_count"] = referred_users.count()
        for referred_user in referred_users:
            orders = referred_user.user.orders.all()
            result["products_bought"] += orders.values("lines__product").count()
            earnings = orders.aggregate(sum=Sum("total_incl_tax"))
            if earnings.get("sum"):
                result["total_earnings"] += earnings["sum"]
        return Response(result)

    @link(permission_classes=[IsAuthenticated], is_for_list=True)
    def applications(self, request):
        """List user's jobs applications."""
        jobs = Job.objects.filter(
            applicants=request.user, submission_deadline__gte=datetime.today()
        )
        page = self.paginate_queryset(jobs)
        if page is not None:
            serializer = JobSerializer(
                jobs, many=True, context={"request": self.request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = JobSerializer(jobs, many=True, context={"request": self.request})
        return Response(serializer.data)


class EducationViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Education CRUD operations."""

    serializer_class = EducationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Education.objects.filter(person__id=self.request.user.id).all()

    def create(self, request, *args, **kwargs):
        request.data["person"] = request.user
        result = super().create(request, *args, **kwargs)
        update_users_profile_percentage(request.user, "educations")
        return result

    def _get_institute_object(self):
        institute_id = self.request.data.get("institute")
        try:
            return Institute.objects.get(id=institute_id)
        except Institute.DoesNotExist:
            raise NotFound("Institue with the id %s not found." % (institute_id))

    def update(self, request, *args, **kwargs):
        user = request.user
        if user.user_type == User.PERSON:
            user = user.person
        else:
            user = user.company
        education_instance = self.get_object()
        if request.data.get("institute"):
            institute = self._get_institute_object()
            request.data["institute"] = institute
        serializer = self.get_serializer(
            education_instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EducationSearchView(HaystackViewSet):
    index_models = [Education]
    serializer_class = EducationSearchSerializer

    def list(self, request, *args, **kwargs):
        if "field_of_study" in request.GET:
            sqs = SearchQuerySet().autocomplete(
                field_of_study_auto=request.GET.get("field_of_study", "")
            )[:5]
        elif "degree" in request.GET:
            sqs = SearchQuerySet().autocomplete(
                degree_auto=request.GET.get("degree", "")
            )[:5]
        else:
            return super().list(request, *args, **kwargs)
        serialized_data = EducationSearchSerializer(sqs, many=True)
        return Response({"results": serialized_data.data})


class ExperienceViewSet(viewsets.ModelViewSet):
    """Experience CRUD operations."""

    serializer_class = ExperienceSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Experience.objects.filter(person__id=self.request.user.id).all()

    def create(self, request, *args, **kwargs):
        request.data["person"] = request.user
        result = super().create(request, *args, **kwargs)
        update_users_profile_percentage(request.user, "experiences")
        return result

    def update(self, request, *args, **kwargs):
        user = request.user
        if user.user_type == User.PERSON:
            user = user.person
        else:
            user = user.company

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ExperienceSearchView(HaystackViewSet):
    index_models = [Experience]
    serializer_class = ExperienceSearchSerializer

    def list(self, request, *args, **kwargs):
        if "production_house" in request.GET:
            sqs = SearchQuerySet().autocomplete(
                production_house_auto=request.GET.get("production_house", "")
            )[:5]
        elif "role" in request.GET:
            sqs = SearchQuerySet().autocomplete(role_auto=request.GET.get("role", ""))[
                :5
            ]
        else:
            return super().list(request, *args, **kwargs)
        serialized_data = ExperienceSearchSerializer(sqs, many=True)
        return Response({"results": serialized_data.data})


class SearchFieldView(HaystackViewSet):
    index_models = [SearchableField]
    serializer_class = SearchableFieldSerializer

    def list(self, request, *args, **kwargs):
        try:
            allowed_keys = SearchableField.objects.values_list(
                "field_name", flat=True
            ).distinct()

            search_fields = list(request.query_params.keys())
            if "limit" in search_fields:
                search_fields.remove("limit")
            if len(search_fields) > 1:
                raise ValidationError("please search with one query only.")
            search_field = search_fields[0]
            if search_field not in allowed_keys:
                raise ValidationError(
                    "allowed keys to search are: {}".format(allowed_keys)
                )
            search_value = request.GET.get(search_field, "")

            sqs = SearchQuerySet().autocomplete(
                value_auto=search_value, field_name=search_field
            )
            serialized_data = SearchableFieldSerializer(sqs, many=True)
            return Response({"results": serialized_data.data})
        except Exception:
            return super().list(request, *args, **kwargs)


class BioViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Bio view set to manage user's bio."""

    serializer_class = BioSerializer
    queryset = Bio.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("data",)

    def update(self, request, *args, **kwargs):
        """Update or create user's bio object."""
        user = request.user
        if user.user_type == User.PERSON:
            user = user.person
        else:
            raise ValidationError(
                "User object other then person type does not have bio."
            )

        # If user's bio does not exist we create it.
        try:
            instance = user.bio
        except Bio.DoesNotExist:
            initial_dict = {
                "eye_color": None,
                "hair_color": None,
                "height": None,
                "waist": None,
                "shoulders": None,
                "chest": None,
                "hips": None,
                "shoe_size": None,
                "hair_style": None,
                "hair_type": None,
                "skin_type": None,
                "body_type": None,
            }
            instance = Bio.objects.create(person=user, data=initial_dict)
        threshold = round(len(instance.data.keys()) * 0.8)
        percentage_before = 0
        for field, value in instance.data.items():
            if value:
                percentage_before += 1
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        percentage_after = 0
        for field, value in instance.data.items():
            if value:
                percentage_after += 1
        if percentage_before < threshold and percentage_after >= threshold:
            increase_percentage(instance.person, "bio")
        # if percentage_before > threshold and percentage_after < threshold:
        #     decrease_percentage(instance.user, "bio")
        return Response(serializer.data)


class LikeViewSet(NestedViewSetMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Likes view set."""

    serializer_class = LikeSerializer
    queryset = Like.objects.all()
    permission_classes = (IsAuthenticated,)


class UserLikeViewSet(LikeViewSet):
    """Favourite users by user and get liked users."""

    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        user_ids = Like.objects.filter(
            sender=self.request.user,
            receiver_content_type=ContentType.objects.get_for_model(User),
        ).values_list("receiver_object_id", flat=True)

        users = User.objects.filter(id__in=user_ids)
        serializer = self.get_serializer(
            users, many=True, context={"request": self.request}
        )
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"request": self.request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            users, many=True, context={"request": self.request}
        )
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """User Can Like other users."""
        contenttype = ContentType.objects.get_for_model(User)
        try:
            User.objects.get(id=kwargs.get("parent_lookup_receiver_object_id"))
        except User.DoesNotExist:
            raise NotFound("User does not exists.")
        obj, liked = Like.like(
            request.user, contenttype, kwargs.get("parent_lookup_receiver_object_id")
        )
        return Response({"liked": liked, "id": obj.receiver_object_id})


class LanguageViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ("language_name",)

    def get_permissions(self):
        if self.request.method == "GET":
            return (AllowAny(),)
        else:
            return (IsAuthenticated(),)

    def update(self, request, *args, **kwargs):
        """Update user's languages."""
        languages = request.data.get("known_languages")
        language_objects = []
        if languages:
            for language in languages:
                language, created = Language.objects.get_or_create(
                    language_name=language
                )
                language_objects.append(language)
        update_users_profile_percentage(request.user, "known_languages")
        request.user.person.known_languages.add(*language_objects)
        result = {"results": request.user.person.known_languages.all().values()}
        return Response(result)


class SkillViewSet(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ("skill_name",)

    def update(self, request, *args, **kwargs):
        """Update user's languages."""
        skills = request.data.get("skills")
        skill_objects = []
        if skills:
            for skill in skills:
                skill, created = Skill.objects.get_or_create(skill_name=skill)
                skill_objects.append(skill)
        update_users_profile_percentage(request.user, "skills")
        request.user.person.skills.add(*skill_objects)
        result = {"results": request.user.person.skills.all().values()}
        return Response(result)


class InstituteViewSet(viewsets.ModelViewSet):
    queryset = Institute.objects.all()
    serializer_class = InstituteSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = (
        "institute_name",
        "id",
    )


class CitiesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name_std",)


class CountriesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = (
        "name",
        "slug",
    )


class UserNotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    User's (unread)notifications.

    This holds ALL notifications
    """

    serializer_class = ActionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Action.objects.filter(actor_object_id=self.request.user.id)


class PasswordResetView(generics.GenericAPIView):
    token_generator = default_token_generator
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """Send password reset email or OTP to user's phone."""
        email = request.data.get("email", None)
        phone_number = request.data.get("phone", None)

        if not email and not phone_number:
            raise ValidationError(
                "Please provide an email address or phone number to proceed to reset password."
            )
        if email:
            user = self.get_user(email)
            context = get_email_context(user)
            if user.first_name:
                context["first_name"] = user.first_name
            else:
                context["first_name"] = None
            context["url"] = django_settings.PASSWORD_RESET_CONFIRM_URL.format(
                **context
            )
            ResetPasswordEmailNotification(user.email, context=context).send()
            return Response({"results": "Reset Password email sucessfully sent."})

        if phone_number:
            user = self.get_user(phone=phone_number)
            try:
                sms_passcode = random.randint(100000, 999999)
                send_sms(
                    phone_number, RESET_PASSWORD_OTP_SMS.format(**{"otp": sms_passcode})
                )
                user.sms_passcode = sms_passcode
                user.save()
                return Response({"success": "Reset Passoword SMS sent successfully."})
            except Exception as e:
                raise e

    def get_user(self, email=None, phone=None):
        try:
            if email:
                user = User._default_manager.get(
                    email__iexact=email, is_active=True, is_superuser=False
                )
            else:
                user = User._default_manager.get(
                    phone=phone, is_active=True, is_superuser=False
                )

        except User.DoesNotExist:
            raise NotFound("User with email %s is not registered." % (email))
        return user


class ActionViewMixin(object):
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            return self.action(serializer)
        else:
            return Response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordResetConfirmView(ActionViewMixin, generics.GenericAPIView):
    """Use this endpoint to finish reset password process."""

    permission_classes = (AllowAny,)
    token_generator = default_token_generator
    serializer_class = PasswordResetConfirmSerializer

    def action(self, serializer):
        serializer.user.set_password(serializer.data["new_password"])
        serializer.user.save()
        return Response(
            {"results": "Your password has been changed successfully."},
            status=status.HTTP_200_OK,
        )


class OTPPasswordResetConfirmView(ActionViewMixin, generics.GenericAPIView):
    """Use this endpoint to finish reset password process."""

    permission_classes = (AllowAny,)
    serializer_class = OTPPasswordResetConfirmSerializer

    def action(self, serializer):
        try:
            user = User.objects.get(sms_passcode=self.request.data["passcode"])
        except User.DoesNotExist:
            raise NotFound("OTP does not match.")

        user.set_password(serializer.data["new_password"])
        user.sms_passcode = None
        user.save()
        return Response(
            {"results": "Your password has been changed successfully."},
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(ActionViewMixin, generics.GenericAPIView):
    permission_classes = (AllowAny,)
    token_generator = default_token_generator
    serializer_class = UidSerializer

    def action(self, serializer):
        if serializer.user.is_email_verified:
            raise ValidationError("Your email id is already verified.")
        serializer.user.is_email_verified = True
        serializer.user.save()
        increase_percentage(serializer.user, "email_verified")
        return Response(
            {"results": "Your email id has been verified successfully."},
            status=status.HTTP_200_OK,
        )


class ContactUsView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Send emails to admins."""

    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        """Send email to admins when users contacts us."""
        subject = request.data.get("subject")
        body = request.data.get("body")
        if not subject:
            raise ValidationError("Subject can not be null.")
        elif not body:
            raise ValidationError("Body can not be null.")
        sender = request.user
        receivers = django_settings.ADMIN_EMAILS
        # TODO: queue this using django rq.
        try:
            send_mail.delay(subject, body, sender, receivers, content_type="html")
        except Exception as e:
            raise e
        return Response("Mail is sent to site admins.")


class ScheduledInvitesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)

    def get_queryset(self):
        return Application.objects.filter(
            job__created_by=self.request.user, state=State.INVITED
        )


class PersonFilter(django_filters.FilterSet):
    skills = django_filters.filters.BaseInFilter(name="skill__skill_name")
    locations = django_filters.filters.BaseInFilter(name="city__name_std")
    gender = django_filters.filters.ChoiceFilter(choices=choices.GENDER_CHOICES)
    min_age = django_filters.MethodFilter()
    max_age = django_filters.MethodFilter()
    bio = django_filters.MethodFilter()
    profile_photo = django_filters.MethodFilter()
    photo_count = django_filters.MethodFilter()
    stageroute_score = django_filters.MethodFilter()

    def filter_stageroute_score(self, queryset, value):
        if value:
            return queryset.filter(stageroute_score__gte=value)
        return queryset

    def filter_photo_count(self, queryset, value):
        if value:
            return queryset.annotate(num=Count("images")).filter(num__gte=value)
        return queryset

    def filter_profile_photo(self, queryset, value):
        if value and value == "true":
            return queryset.exclude(images=None)
        elif value and value == "false":
            return queryset.filter(images=None)
        return queryset

    def filter_bio(self, queryset, value):
        if value:
            # try to convert string to dict
            try:
                value = ast.literal_eval(value)
            except Exception as e:
                raise e

            return queryset.filter(bio__data__contains=value)
        return queryset

    def filter_min_age(self, queryset, value):
        """Value is age.

        we calculate years back and find the date.
        we find all the birth dates greater than this date so min age
        criteria if satisfied.
        """
        if value:
            birth_date_upper_limit = datetime.today() - relativedelta(years=int(value))
            return queryset.filter(date_of_birth__lte=birth_date_upper_limit.date())
        return queryset

    def filter_max_age(self, queryset, value):
        if value:
            birth_date_lower_limit = datetime.today() - relativedelta(
                years=int(value) + 1
            )
            return queryset.filter(date_of_birth__gte=birth_date_lower_limit.date())
        return queryset

    class Meta:
        model = Person


class PersonViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()
    permission_classes = (AllowAny,)
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    ordering_fields = (
        "date_joined",
        "stageroute_score",
        "profile_completion_percentage",
    )
    # default order for persons listing.
    ordering = ("-date_joined",)
    filter_class = PersonFilter
    search_fields = (
        "=email",
        "=phone",
        "first_name",
        "last_name",
    )


class UserPreferenceView(generics.UpdateAPIView, generics.ListCreateAPIView):
    serializer_class = UserPreferenceSerializer
    queryset = UserPreference.objects.all()

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response(self.get_serializer(user.preferences).data)

    def update(self, request, *args, **kwargs):
        """Update or create user's bio object."""
        user = request.user
        instance = user.preferences
        if "search_preference" in request.data:
            for key in request.data["search_preference"].keys():
                if key in instance.search_preference.keys():
                    instance.search_preference.pop(key)
            request.data["search_preference"].update(instance.search_preference)
        #     try:
        #         validate(request.data["search_preference"], schema)
        #     except Exception as e:
        #         raise ValidationError("Not valid schema: %s." % (e.message))
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserEarningsView(generics.ListAPIView):
    def _filter_transactions(self, transactions, merchant_reference):
        return transactions.filter(
            transfer__merchant_reference__contains=merchant_reference
        )

    def _total_amount(self, transactions):
        amount = transactions.aggregate(sum=Sum("amount")).get("sum")
        return 0 if not amount else amount

    def get(self, request, *args, **kwargs):
        is_casting_director = is_user_casting_director(request.user)
        if is_casting_director:
            transactions = Transaction.objects.filter(
                account__primary_user=request.user
            )
            start_date_string = request.GET.get("start_date")
            if start_date_string:
                start_date = string_to_date(start_date_string)
            else:
                start_date = date(datetime.now().year, datetime.now().month, 1)

            end_date_string = request.GET.get("end_date")
            if end_date_string:
                end_date = string_to_date(end_date_string)
            else:
                end_date = last_day_of_month(datetime.now().date())

            transactions = transactions.filter(
                date_created__gte=start_date, date_created__lte=end_date
            )
            job_post_transactions = self._filter_transactions(transactions, "job_post")
            job_post_earnings = self._total_amount(job_post_transactions)

            paid_users_transactions = self._filter_transactions(
                transactions, "user_paid"
            )
            paid_users_earnings = self._total_amount(paid_users_transactions)

            application_transactions = self._filter_transactions(
                transactions, "application"
            )
            application_earnings = self._total_amount(application_transactions)

            jobs = {}
            posted_jobs = Job.objects.filter(
                created_by=request.user,
                created_at__gte=start_date,
                created_at__lte=end_date,
            )
            # jobs count
            jobs["approved"] = posted_jobs.filter(status=choices.APPROVED).count()
            jobs["removed"] = posted_jobs.filter(status=choices.REMOVED).count()
            jobs["pendin_approval"] = posted_jobs.filter(
                status=choices.PENDING_APPROVAL
            ).count()
            jobs["closed"] = posted_jobs.filter(status=choices.CLOSED).count()
            referred_users = ReferralResponse.objects.filter(
                referral__in=request.user.referral_codes.all()
            )
            # application count
            applications = (
                Application.objects.filter(job__in=posted_jobs)
                .exclude(state__in=[State.PIPELINED, State.IGNORED])
                .count()
            )
            paid_users_count = referred_users.filter(
                action="CASTING_DIRECTOR_PAID"
            ).count()

            results = {
                "earnings_jobs": job_post_earnings,
                "earnings_applications": application_earnings,
                "posted_jobs": jobs,
                "applications": applications,
                "paid_users": paid_users_count,
                "earnings_paid_registraions": paid_users_earnings,
            }
            return Response({"results": results})
        else:
            raise ValidationError("No permission to view earnings.")


class ApplicationsOnJobsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsCastingDirector,)
    serializer_class = ApplicationDetailSerializer
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.OrderingFilter,
    )
    filter_fields = (
        "state",
        "job_id",
    )
    ordering_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_queryset(self):
        applications = Application.objects.filter(
            job__created_by=self.request.user
        ).exclude(state__in=[State.IGNORED, State.PIPELINED])
        return applications


class VerificationActivitiesViewSet(viewsets.GenericViewSet):
    def send_otp_sms(self, request, *args, **kwargs):
        """Send otp sms to user."""
        user = request.user
        phone_number = user.phone
        if phone_number:
            if not user.is_phone_verified:
                try:
                    sms_passcode = random.randint(100000, 999999)
                    send_sms(phone_number, OTP_SMS.format(**{"otp": sms_passcode}))
                    user.sms_passcode = sms_passcode
                    user.save()
                    return Response({"success": "SMS passcode sent successfully."})
                except Exception as e:
                    raise e
            else:
                raise ValidationError("User's phone number is already verified.")
        else:
            raise NotFound("User's phone number does not exists.")

    def verify_phone(self, request, pk=None):
        """Verify user's phone."""
        user = request.user
        if user.is_phone_verified:
            return Response({"response": "user's phone number is already verified"})
        elif not user.phone:
            raise NotFound("user's phone number does not exists.")

        elif "passcode" not in request.data:
            raise NotFound("You did not enter a passcode to verify your number.")

        else:
            data = request.data.copy()
            try:
                passcode_entered = int(data["passcode"])
            except ValueError:
                return Response(
                    {"response": "Please enter passcode with numbers only."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                raise e

            if passcode_entered == user.sms_passcode:
                user.is_phone_verified = True
                user.sms_passcode = None
                # TODO: MobileVerificationNotification
                user.save()
                increase_percentage(user, "phone_verified")
                return Response(
                    {
                        "response": "Thank you for verifying your phone number.",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"response": "passcode entered is invalid."},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class CheckUserView(viewsets.GenericViewSet):
    permission_classes = (
        IsAuthenticated,
        IsCastingDirector,
    )
    serializer_class = UserSerializer

    def check(self, request, *args, **kwargs):
        """Check if user exists or not."""
        data = request.data.copy()
        email = data.get("email")
        phone = data.get("phone")

        if email is None and phone is None:
            raise ValidationError("Please provide email or phone to check existance.")
        if email == "":
            raise ValidationError("Email field can not be blank.")
        if phone == "":
            raise ValidationError("Phone field can not be blank.")
        if email and phone:
            raise ValidationError("Please enter either email or phone.")
        if email:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                raise NotFound("User does not exist.")
        if phone:
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                raise NotFound("User does not exist.")
        serializer = self.get_serializer(user)
        result = serializer.data
        result["token"] = user.auth_token.key
        return Response(result)


class NotifyUserView(generics.GenericAPIView):
    permission_classes = (IsSupportGroupMember,)

    def post(self, request, *args, **kwargs):

        data = request.data.copy()
        email = data.get("email")
        phone = data.get("phone")
        uid = data.get("uid")
        if not any([email, phone, uid]):
            raise ValidationError(
                detail="At least one of email, phone or uid is required."
            )
        if uid:
            # if user id is given it is given highest priority so we send email, sms to his/her email and phone only.
            try:
                user = User.objects.get(id=uid)
            except User.DoesNotExist:
                raise NotFound("User Not Found.")
            email = user.email
            phone = user.phone

        if email:
            subject = request.data.get("subject")
            email_message = request.data.get("email_message")
            if not all([subject, email_message]):
                raise ValidationError(
                    "Subject and email_message both required to send an email."
                )
            context = {"subject": subject, "email_message": email_message}
            NotifyUser(email, context=context).send()
        if phone:
            sms_message = request.data.get("sms_message")
            if not sms_message:
                raise ValidationError("sms_message is required to send an sms.")
            send_sms(phone, sms_message)
        return Response({"result": "Success"})
