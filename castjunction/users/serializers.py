"""Serializers for user sign up and login."""
import re

from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.utils import email_address_exists
from allauth.socialaccount.models import SocialToken

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import ugettext_lazy as _
from cities.models import City, Country

from rest_auth.serializers import (
    LoginSerializer as BaseLoginSerializer,
    TokenSerializer as BaseTokenSerializer,
)
from rest_auth.registration.serializers import SocialLoginSerializer
from rest_auth.social_serializers import (
    TwitterLoginSerializer as BaseTwitterLoginSerializer,
)
from rest_auth.models import TokenModel
from rest_framework import exceptions, serializers

from rest_framework_hstore.serializers import HStoreSerializer

from utils import app_settings, choices
from utils.utils import ChoicesField, create_referral, get_referrer_user
from drf_haystack.serializers import HaystackSerializerMixin
from requests.exceptions import HTTPError
from rest_framework_extensions.serializers import PartialUpdateSerializerMixin
from pinax.likes.models import Like
from pinax.referrals.models import ReferralResponse
from jsonschema import validate

from project.serializers import DynamicFieldsModelSerializer
from multimedia.serializers import ImageSerializer

from custom_oscarapi.serializers import ProductSerializer
from oscar.core.loading import get_model
from .models import (
    Company,
    CompanyType,
    Person,
    PersonType,
    User,
    Bio,
    SearchableField,
    Education,
    Experience,
    Skill,
    Institute,
    Language,
    UserPreference,
)
from .jsonschemas import schema
from .search_indexes import EducationIndex, ExperienceIndex, SearchableFieldIndex
from .utils import decode_uid
from .adapters import complete_social_login

Product = get_model("catalogue", "Product")


class TokenSerializer(BaseTokenSerializer):
    """Serializer for Token model."""

    user_id = serializers.IntegerField(source="user.id")
    email = serializers.CharField(source="user.email")
    first_name = serializers.CharField(source="user.first_name")
    location = serializers.CharField(source="user.city")
    image = serializers.ImageField(source="user.person.images")
    referral_code = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        """Meta."""

        model = TokenModel
        fields = (
            "key",
            "user_id",
            "email",
            "first_name",
            "image",
            "location",
            "referral_code",
            "permissions",
        )

    def get_image(self, obj):
        if obj.user.user_type == User.PERSON:
            image = obj.user.person.images.filter(image_type=choices.PRIMARY).last()
        else:
            image = obj.user.company.images.filter(image_type=choices.PRIMARY).last()
        serializer = ImageSerializer(
            image, context={"request": self.context["request"]}
        )
        return serializer.data

    def get_referral_code(self, obj):
        if obj.user.referral_codes.exists():
            return obj.user.referral_codes.values("code")[0]["code"]
        return None

    def get_permissions(self, obj):
        return obj.user.user_permissions.values("codename", "name")


class InstituteSerializer(serializers.ModelSerializer):
    location = serializers.SlugRelatedField(
        slug_field="name_std", required=False, queryset=City.objects.all()
    )

    class Meta:
        model = Institute
        fields = ("id", "institute_name", "established_year", "location")
        extra_kwargs = {
            "institute_name": {"required": True},
        }


class BioSerializer(HStoreSerializer):

    data = serializers.DictField()

    class Meta:
        model = Bio
        fields = (
            "id",
            "data",
        )

    def validate_data(self, value, **kwargs):
        """Will raise validation error input data is not according to defined schema."""
        try:
            validate(value, schema)
            return value
        except Exception as e:
            raise serializers.ValidationError("Not valid schema: %s." % (e.message))

    def update(self, instance, validated_data):
        validated_data = validated_data.get("data")
        if validated_data:
            for attr, value in validated_data.items():
                if value is not None:
                    setattr(instance, attr, value)
            instance.save()
        return instance


class EducationSerializer(serializers.ModelSerializer):
    institute = serializers.PrimaryKeyRelatedField(queryset=Institute.objects.all())
    institute_name = serializers.SerializerMethodField()

    class Meta:
        model = Education

        extra_kwargs = {
            "person": {"write_only": True},
        }

    def get_institute_name(self, obj):
        return obj.institute.institute_name

    def update(self, instance, validated_data):

        allowed_fields = [
            "institute",
            "start_date",
            "end_date",
            "degree",
            "grade",
            "social_activites",
            "field_of_study",
            "description",
        ]

        for attr, value in validated_data.items():
            if (attr in allowed_fields) and (value is not None):
                setattr(instance, attr, value)
        instance.save()
        return instance


class EducationSearchSerializer(HaystackSerializerMixin, EducationSerializer):
    class Meta(EducationSerializer.Meta):
        index_classes = [EducationIndex]


class ExperienceSerializer(serializers.ModelSerializer):
    experience_type = ChoicesField(choices=Experience.EXPERIENCE_TYPE)
    location = serializers.SlugRelatedField(
        slug_field="name_std", queryset=City.objects.all()
    )

    class Meta:
        model = Experience
        index_classes = [ExperienceIndex]
        extra_kwargs = {
            "production_house": {"required": False},
        }

    def update(self, instance, validated_data):
        allowed_fields = [
            "production_house",
            "title",
            "role",
            "character_name",
            "experience_type",
            "start_date",
            "end_date",
            "description",
            "location",
        ]

        for attr, value in validated_data.items():
            if (attr in allowed_fields) and (value is not None):
                setattr(instance, attr, value)
        instance.save()
        return instance


class ExperienceSearchSerializer(HaystackSerializerMixin, ExperienceSerializer):
    class Meta(ExperienceSerializer.Meta):
        index_classes = [ExperienceIndex]


class SearchableFieldSerializer(HaystackSerializerMixin, serializers.ModelSerializer):
    class Meta:
        index_classes = [SearchableFieldIndex]
        model = SearchableField


class SkillSerializer(serializers.ModelSerializer):
    """Skill serializer."""

    class Meta:
        """Meta."""

        model = Skill
        fields = ("skill_name",)

    def to_representation(self, data):
        """Show skill name while serializing."""
        return data.skill_name


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        exclude = ("person", "id")

    def to_representation(self, data):
        return data.language_name


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        exclude = (
            "kind",
            "alt_names",
        )


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        exclude = (
            "neighbours",
            "alt_names",
        )


class UserPartialSerializer(DynamicFieldsModelSerializer):
    city = serializers.SlugRelatedField(
        slug_field="name_std", required=False, queryset=City.objects.all()
    )
    nationality = serializers.SlugRelatedField(
        slug_field="name", queryset=Country.objects.all()
    )
    profile_photo = serializers.SerializerMethodField()
    cover_photo = serializers.SerializerMethodField()
    user_images = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Meta for UserSerializer."""

        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "date_of_birth",
            "email_daily_updates",
            "city",
            "nationality",
            "date_joined",
            "profile_photo",
            "age",
            "is_profile_approved",
            "is_email_verified",
            "is_phone_verified",
            "profile_completion_percentage",
            "stageroute_score",
            "cover_photo",
            "user_images",
            "likes",
            "interested_professions",
        )
        read_only_fields = ("email",)

    def get_profile_photo(self, obj):
        if obj.user_type == User.PERSON:
            image = obj.person.images.filter(image_type=choices.PRIMARY).last()
        else:
            image = obj.company.images.filter(image_type=choices.PRIMARY).last()
        serializer = ImageSerializer(
            image, context={"request": self.context["request"]}
        )
        return serializer.data

    def get_cover_photo(self, obj):
        if obj.user_type == User.PERSON:
            image = obj.person.images.filter(image_type=choices.COVER).last()
        else:
            image = obj.company.images.filter(image_type=choices.COVER).last()
        serializer = ImageSerializer(
            image, context={"request": self.context["request"]}
        )
        return serializer.data

    def get_user_images(self, obj):
        if obj.user_type == User.PERSON:
            images = obj.person.images.filter(image_type=choices.GENERIC)[:4]
        else:
            images = obj.company.images.filter(image_type=choices.GENERIC)[:4]
        if images:
            serializer = ImageSerializer(
                images, many=True, context={"request": self.context["request"]}
            )
            return serializer.data
        return None

    def get_likes(self, obj):
        try:
            if "request" in self.context:
                user = self.context["request"].user
                like = Like.objects.filter(
                    sender=user,
                    receiver_content_type=ContentType.objects.get_for_model(User),
                    receiver_object_id=obj.id,
                )
                if like:
                    return True
        except:
            pass
        return False


class UserSerializer(UserPartialSerializer):
    """Serialize user objects."""

    class Meta:
        """Meta for UserSerializer."""

        model = User
        fields = UserPartialSerializer.Meta.fields + (
            "email",
            "phone",
        )
        read_only_fields = ("email",)


# Get the UserModel
UserModel = get_user_model()


class PersonPartialSerializer(UserPartialSerializer):
    gender = ChoicesField(choices=choices.GENDER_CHOICES)
    bio = BioSerializer(read_only=True)
    skills = SkillSerializer(many=True)
    educations = EducationSerializer(many=True)
    experiences = ExperienceSerializer(many=True)
    known_languages = serializers.SlugRelatedField(
        slug_field="language_name", queryset=Language.objects.all(), many=True
    )

    class Meta:
        model = Person
        fields = UserPartialSerializer.Meta.fields + (
            "phone",
            "gender",
            "bio",
            "associated_with_agent",
            "skills",
            "educations",
            "experiences",
            "known_languages",
        )
        related_fields = ["bio"]

    def get_gender(self, obj):
        return obj.get_gender_display()

    def update(self, instance, validated_data):
        restricted_fields = ["password"]
        for attr, value in validated_data.items():
            if (attr not in restricted_fields) and (value is not None):
                setattr(instance, attr, value)
        instance.save()
        return instance


class PersonSerializer(PersonPartialSerializer):
    class Meta:
        model = Person
        fields = PersonPartialSerializer.Meta.fields + (
            "email",
            "phone",
        )
        related_fields = ["bio"]


class CompanyPartialSerializer(UserPartialSerializer):
    class Meta:
        model = Company
        fields = UserPartialSerializer.Meta.fields


class CompanySerializer(CompanyPartialSerializer):
    class Meta:
        model = Company
        fields = CompanyPartialSerializer.Meta.fields + (
            "company_email",
            "company_phone",
            "company_website",
        )


class TwitterLoginSerializer(BaseTwitterLoginSerializer):
    """Custom twitter login serializer."""

    account_type = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Validate social login user."""
        view = self.context.get("view")
        request = self._get_request()

        if not view:
            raise serializers.ValidationError(
                "View is not defined, pass it as a context variable"
            )

        adapter_class = getattr(view, "adapter_class", None)
        if not adapter_class:
            raise serializers.ValidationError("Define adapter_class in view")

        adapter = adapter_class()
        app = adapter.get_provider().get_app(request)

        if ("access_token" in attrs) and ("token_secret" in attrs):
            access_token = attrs.get("access_token")
            token_secret = attrs.get("token_secret")
        else:
            raise serializers.ValidationError(
                "Incorrect input. access_token and token_secret are required."
            )

        request.session["oauth_api.twitter.com_access_token"] = {
            "oauth_token": access_token,
            "oauth_token_secret": token_secret,
        }
        token = SocialToken(token=access_token, token_secret=token_secret)
        token.app = app

        if "account_type" in attrs:
            account_type = attrs.get("account_type")
        else:
            account_type = "talent"
        try:
            login, response = CustomSocialLoginSerializer.get_social_login(
                self, adapter, app, token, access_token, account_type
            )
            # Temp fix because twitter response email is not coming.
            if login.user.email == "":
                login.user.email = None
            complete_social_login(request, login, response)
        except HTTPError:
            raise serializers.ValidationError("Incorrect value")

        if not login.is_existing:
            login.lookup()
            login.save(request, connect=True)

        data = RegisterSerializer().validate_account_type(account_type=account_type)
        user_account_type = list(data.values())[0]

        try:
            temp_user = login.account.user.person
            typ, created = PersonType.objects.get_or_create(
                person_type=user_account_type
            )
        except User.DoesNotExist:
            temp_user = login.account.user.company
            typ, created = CompanyType.objects.get_or_create(
                company_type=user_account_type
            )
        temp_user.typ.add(typ)

        referral = create_referral(temp_user)
        temp_user.referral = referral
        # provide incentive to user who referred this user.

        request = self.context.get("request")
        if request and "referral_code" in request.data:
            referrer_user = get_referrer_user(request, user=temp_user)

        attrs["user"] = login.account.user

        return attrs


class CustomSocialLoginSerializer(SocialLoginSerializer):
    """Custom social login serializer to accept account type."""

    account_type = serializers.CharField(required=False, allow_blank=True)

    def get_social_login(self, adapter, app, token, response, account_type):
        """
        :param adapter: allauth.socialaccount Adapter subclass. Usually OAuthAdapter or Auth2Adapter.

        :param app: `allauth.socialaccount.SocialApp` instance
        :param token: `allauth.socialaccount.SocialToken` instance
        :param response: Provider's response for OAuth1. Not used in the
        :return: :return: A populated instance of the `allauth.socialaccount.SocialLoginView` instance
        """
        request = self._get_request()
        kwargs = {"response": response, "account_type": account_type}
        social_login, response = adapter.complete_login(request, app, token, **kwargs)
        social_login.token = token

        return social_login, response

    def validate(self, attrs):
        """Validate social login user."""
        view = self.context.get("view")
        request = self._get_request()

        if not view:
            raise serializers.ValidationError(
                _("View is not defined, pass it as a context variable")
            )

        adapter_class = getattr(view, "adapter_class", None)
        if not adapter_class:
            raise serializers.ValidationError(_("Define adapter_class in view"))

        adapter = adapter_class()
        app = adapter.get_provider().get_app(request)

        # More info on code vs access_token
        # http://stackoverflow.com/questions/8666316/facebook-oauth-2-0-code-and-token

        # Case 1: We received the access_token
        if "access_token" in attrs:
            access_token = attrs.get("access_token")

        # Case 2: We received the authorization code
        elif "code" in attrs:
            self.callback_url = getattr(view, "callback_url", None)
            self.client_class = getattr(view, "client_class", None)

            if not self.callback_url:
                raise serializers.ValidationError(_("Define callback_url in view"))
            if not self.client_class:
                raise serializers.ValidationError(_("Define client_class in view"))

            code = attrs.get("code")

            provider = adapter.get_provider()
            scope = provider.get_scope(request)
            client = self.client_class(
                request,
                app.client_id,
                app.secret,
                adapter.access_token_method,
                adapter.access_token_url,
                self.callback_url,
                scope,
            )
            token = client.get_access_token(code)
            access_token = token["access_token"]

        else:
            raise serializers.ValidationError(
                _("Incorrect input. access_token or code is required.")
            )

        token = adapter.parse_token({"access_token": access_token})
        token.app = app

        if "account_type" in attrs:
            account_type = attrs.get("account_type")
        else:
            account_type = "talent"

        try:
            login, response = self.get_social_login(
                adapter, app, token, access_token, account_type
            )
            complete_social_login(request, login, response)
        except HTTPError:
            raise serializers.ValidationError(_("Incorrect value"))

        if not login.is_existing:
            login.lookup()
            login.save(request, connect=True)

        data = RegisterSerializer().validate_account_type(account_type=account_type)
        user_account_type = list(data.values())[0]

        try:
            temp_user = login.account.user.person
            typ, created = PersonType.objects.get_or_create(
                person_type=user_account_type
            )
        except User.DoesNotExist:
            temp_user = login.account.user.company
            typ, created = CompanyType.objects.get_or_create(
                company_type=user_account_type
            )
        temp_user.typ.add(typ)

        referral = create_referral(temp_user)
        temp_user.referral = referral
        # provide incentive to user who referred this user.

        request = self.context.get("request")
        if request and "referral_code" in request.data:
            referrer_user = get_referrer_user(request, user=temp_user)
        attrs["user"] = login.account.user

        return attrs


class LoginSerializer(BaseLoginSerializer):
    """Login using phone number of email."""

    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(style={"input_type": "password"})

    def _validate_email_phone(self, email, phone, password):
        user = None

        if email and password:
            user = authenticate(email=email, password=password)

        elif phone and password:
            user = authenticate(phone=phone, password=password)
        else:
            msg = _('Must include either or "email" or "phone" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def validate(self, attrs):
        """Validate user input."""
        username = attrs.get("username")
        pattern = re.compile("^\d{10,13}")
        match = pattern.match(username)
        email = None
        phone = None
        user = None
        if match:
            phone = username
        else:
            email = username
        password = attrs.get("password")
        if "allauth" in settings.INSTALLED_APPS:

            from utils import app_settings

            # Authentication through email
            if (
                app_settings.AUTHENTICATION_METHOD
                == app_settings.AuthenticationMethod.EMAIL
            ):
                user = super()._validate_email(email, password)

            # Authentication through either phone number or email
            else:
                user = self._validate_email_phone(email, phone, password)

        else:
            # Authentication without using allauth
            if email:
                try:
                    username = UserModel.objects.get(email__iexact=email).get_username()
                except UserModel.DoesNotExist:
                    pass

            if username:
                user = self._validate_username_email(username, "", password)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                msg = _("User account is disabled.")
                raise exceptions.ValidationError(msg)
        else:
            msg = _("Unable to log in with provided credentials.")
            raise exceptions.ValidationError(msg)

        # If required, is the email verified?
        if "rest_auth.registration" in settings.INSTALLED_APPS:
            from allauth.account import app_settings

            if (
                app_settings.EMAIL_VERIFICATION
                == app_settings.EmailVerificationMethod.MANDATORY
            ):
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    raise serializers.ValidationError(_("E-mail is not verified."))

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.Serializer):
    """Sign up user using phone or email."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=False, write_only=True)
    account_type = serializers.CharField(required=True)
    full_name = serializers.CharField(required=True)
    phone = serializers.CharField(required=False)
    gender = ChoicesField(choices=choices.GENDER_CHOICES, default=choices.NOT_SPECIFIED)

    valid_account_types = {
        User.PERSON: [
            PersonType.TALENT,
            PersonType.DIRECTOR,
            PersonType.CASTING_DIRECTOR,
        ],
        User.COMPANY: [CompanyType.PRODUCTION_HOUSE],
    }

    def phone_number_exists(self, phone):
        """If user exists with phone number return True else return False."""
        try:
            User.objects.get(phone=phone)
        except User.DoesNotExist:
            return False
        return True

    def validate_account_type(self, account_type):
        """Valid account type."""
        account_type = account_type.lower()
        if account_type in self.valid_account_types[User.PERSON]:
            return {User.PERSON: account_type}
        elif account_type in self.valid_account_types[User.COMPANY]:
            return {User.COMPANY: account_type}
        else:
            raise serializers.ValidationError(
                _(
                    "Account type field must be string value, accepted values are {0}".format(
                        self.valid_account_types
                    )
                )
            )

    def validate_phone(self, phone):
        """Validate phone number."""
        if self.phone_number_exists(phone):
            raise serializers.ValidationError(
                "A user is already registered with this phone number."
            )
        return phone

    def validate_username(self, username):
        """Check for unique email address or phone number."""
        pattern = re.compile("^\d{10,13}")
        match = pattern.match(username)
        if match:
            username = self.validate_phone(username)
            # TODO: validate phone
            return username
        else:
            email = get_adapter().clean_email(username)
            if app_settings.UNIQUE_EMAIL:
                if email and email_address_exists(email):
                    raise serializers.ValidationError(
                        "A user is already registered with this e-mail address."
                    )
            return email

    def validate_password(self, password):
        """Check for password length."""
        return get_adapter().clean_password(password)

    def validate(self, data):
        """Validate."""
        return data

    def new_user(self, request):
        """New user object of either Person or Company class."""
        account_type = list(self.cleaned_data.get("account_type").keys())[0]
        if account_type == "P":
            user = Person()
        else:
            user = Company()
        return user

    def custom_signup(self, request, user, commit=True):
        """Sign up for person or company using data provided."""
        # user can be either Company or Person object.
        from allauth.account.utils import user_email

        data = self.cleaned_data

        if data.get("full_name"):
            try:
                first_name, last_name = data.get("full_name").split(" ", 1)
            except ValueError:
                first_name, last_name = data.get("full_name"), None
            user.first_name = first_name
            user.last_name = last_name
        if data.get("phone"):
            user.phone = data.get("phone")
        if data.get("gender"):
            user.gender = data.get("gender")
        username = data.get("username")
        pattern = re.compile("^\d{10,13}")
        match = pattern.match(username)
        if match:
            user.phone = username
        else:
            user_email(user, username)
        password_set_by_user = True
        password = data.get("password")
        if (password == "") or (password is None):
            password_set_by_user = False
            password = User.objects.make_random_password()

        user.set_password(password)
        # self.populate_username(request, user)
        if commit:
            # Ability not to commit makes it easier to derive from
            # this adapter by adding
            user.save()

        referral = create_referral(user)
        user.referral = referral
        # provide incentive to user who referred this user.
        request = self.context.get("request")
        if request and "referral_code" in request.data:
            referrer_user = get_referrer_user(request, user=user)

        user.save()
        # saving user_type and person or company's type depending on user object.
        user.user_type = list(data["account_type"].keys())[0]

        user_account_type = list(data["account_type"].values())[0]

        if user.user_type == User.COMPANY:
            typ, created = CompanyType.objects.get_or_create(
                company_type=user_account_type
            )
        elif user.user_type == User.PERSON:
            typ, created = PersonType.objects.get_or_create(
                person_type=user_account_type
            )
        user.typ.add(typ)

        # send password to post_save signal so add it in email context
        if not password_set_by_user:
            user._password = password

        return user

    def get_cleaned_data(self):
        """Return username password account_type dict."""
        return {
            "username": self.validated_data.get("username", ""),
            "password": self.validated_data.get("password", ""),
            "account_type": self.validated_data.get("account_type", ""),
            "full_name": self.validated_data.get("full_name", ""),
            "gender": self.validated_data.get("gender", ""),
            "phone": self.validated_data.get("phone", ""),
        }

    def save(self, request):
        """Called by perform_create()."""
        # adapter = get_adapter()
        self.cleaned_data = self.get_cleaned_data()
        user = self.new_user(request)
        # adapter.save_user(request, user, self)
        self.custom_signup(request, user)
        setup_user_email(request, user, [])
        return user


class LikeSerializer(PartialUpdateSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Like


class UidSerializer(serializers.Serializer):
    uid = serializers.CharField()

    default_error_messages = {
        "invalid_uid": "invalid uid",
    }

    def validate_uid(self, value):
        try:
            uid = decode_uid(value)
            self.user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError(self.error_messages["invalid_uid"])
        return value


class UidAndTokenSerializer(UidSerializer):
    token = serializers.CharField()

    default_error_messages = {
        "invalid_token": "invalid token",
        "invalid_uid": "invalid uid",
    }

    def validate(self, attrs):
        attrs = super(UidAndTokenSerializer, self).validate(attrs)

        if not self.context["view"].token_generator.check_token(
            self.user.person, attrs["token"]
        ):
            raise serializers.ValidationError(self.error_messages["invalid_token"])
        return attrs


class PasswordResetConfirmSerializer(UidAndTokenSerializer):

    new_password = serializers.CharField(
        style={"input_type": "password"}, validators=[]
    )

    re_new_password = serializers.CharField()

    default_error_messages = {
        "password_mismatch": "The two password fields didn't match.",
    }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs["new_password"] != attrs["re_new_password"]:
            raise serializers.ValidationError(self.error_messages["password_mismatch"])
        return attrs

    def validate_new_password(self, password):
        min_length = app_settings.PASSWORD_MIN_LENGTH

        if len(password) < min_length:
            raise serializers.ValidationError(
                "Password must be a minimum of {0} " "characters.".format(min_length)
            )
        return password


class OTPPasswordResetConfirmSerializer(serializers.Serializer):

    new_password = serializers.CharField(
        style={"input_type": "password"}, validators=[]
    )

    re_new_password = serializers.CharField()

    default_error_messages = {
        "password_mismatch": "The two password fields didn't match.",
    }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs["new_password"] != attrs["re_new_password"]:
            raise serializers.ValidationError(self.error_messages["password_mismatch"])
        return attrs

    def validate_new_password(self, password):
        min_length = app_settings.PASSWORD_MIN_LENGTH

        if len(password) < min_length:
            raise serializers.ValidationError(
                "Password must be a minimum of {0} " "characters.".format(min_length)
            )
        return password


class ReferralResponseSerializer(serializers.ModelSerializer):
    """Referrals of user."""

    user = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()

    class Meta:
        """Meta."""

        model = ReferralResponse

    def get_user(self, obj):
        return UserSerializer(
            obj.user, context={"request": self.context["request"]}
        ).data

    def get_product(self, obj):
        order = obj.user.orders.first()
        if order:
            product_ids = order.lines.values_list("product_id", flat=True)
            products = Product.objects.filter(id__in=product_ids)
            return ProductSerializer(
                products, context={"request": self.context["request"]}, many=True
            ).data
        return None


class UserPreferenceSerializer(serializers.ModelSerializer):
    profile_state = ChoicesField(choices=choices.PROFILE_STATE_CHOICES)

    class Meta:
        model = UserPreference
        exclude = ("user",)
