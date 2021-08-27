"""Commong settings for castjunction."""
import os
import environ
from os.path import join
from oscar.defaults import *

from decimal import Decimal
from oscar import get_core_apps
from oscar import OSCAR_MAIN_TEMPLATE_DIR
from oscar.defaults import OSCAR_DASHBOARD_NAVIGATION
from oscar_accounts import TEMPLATE_DIR as ACCOUNTS_TEMPLATE_DIR

root = environ.Path(__file__) - 2  # three folder back (/a/b/c/ - 3 = /)
BASE_DIR = root()

env = environ.Env(
    DEBUG=(bool, True),
)  # set default values and casting


INSTALLED_APPS = (
    "grappelli",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.gis",
    "django.contrib.flatpages",
    # Third party apps
    "oscar_accounts",
    "imagekit",
    "reversion",
    "django_rq",  # asynchronous queuing
    "django_extensions",
    "push_notifications",
    "rest_framework_docs",
    "django_hstore",
    "corsheaders",
    "django_fsm",
    "pinax.referrals",
    "pinax.likes",
    "widget_tweaks",
    "postman",
    "django_ses",
    "field_history",
    "hvad",
    "review",
    "user_media",
    "generic_positions",
    # auth
    "rest_framework",  # utilities for rest apis
    "rest_framework.authtoken",  # token authentication
    "rest_auth",
    "allauth",
    "allauth.account",
    "rest_auth.registration",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.twitter",
    "allauth.socialaccount.providers.google",
    # regarding countries and cities
    "cities",
    # Your apps
    "authentication",
    "users",
    "project",
    "application",
    "multimedia",
    "drip",
    "user_tokens",
    "notifications",
    "custom_oscarapi",
    # safest to add as last app
    "actstream",
) + tuple(get_core_apps())

OSCAR_DASHBOARD_NAVIGATION.append(
    {
        "label": "Accounts",
        "icon": "icon-globe",
        "children": [
            {
                "label": "Accounts",
                "url_name": "accounts-list",
            },
            {
                "label": "Transfers",
                "url_name": "transfers-list",
            },
            {
                "label": "Deferred income report",
                "url_name": "report-deferred-income",
            },
            {
                "label": "Profit/loss report",
                "url_name": "report-profit-loss",
            },
        ],
    }
)

ACCOUNTS_UNIT_NAME = "Token"
ACCOUNTS_UNIT_NAME_PLURAL = "Tokens"
ACCOUNTS_MIN_LOAD_VALUE = Decimal("30.00")
ACCOUNTS_MAX_ACCOUNT_VALUE = Decimal("1000.00")
ACCOUNT_ADAPTER = "users.adapters.MyAccountAdapter"
TOKEN_ACCOUNT = "token_account"
REIMBURSEMENT_ACCOUNT = "reimbursement_account"
ACCOUNT_INTIAL_BALANCE = Decimal("0.0")
# preset values
CA_INCENTIVE_THRESHOLD = 7
CREDIT_TOKEN_VALUE = 50
AUTHENTICATION_BACKENDS = (
    "utils.backend.CustomAuthBackend",
    # fallback to default authentication backend if first fails
    "django.contrib.auth.backends.ModelBackend",
    "pinax.likes.auth_backends.CanLikeBackend",
)
# https://docs.djangoproject.com/en/1.8/topics/http/middleware/
MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
)

ROOT_URLCONF = "urls"

SECRET_KEY = "Not a secret"
WSGI_APPLICATION = "wsgi.application"

# Email
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_PORT = 25
# EMAIL_HOST_USER = ''
# EMAIL_HOST_PASSWORD = ''
# EMAIL_USE_TLS = False
EMAIL_BACKEND = "django_ses.SESBackend"

EMAIL_DEFAULT_SITE_NAME = "Stageroute"
EMAIL_ASSESSMENT_SITE_NAME = "Stageroute"
DEFAULT_FROM_EMAIL = "Brajesh at StageRoute <brajesh.s@stageroute.com>"
STAGEROUTE_EMAIL = "StageRoute Team <team@stageroute.com>"

#######
# AWS #
#######
AWS_ACCESS_KEY_ID = "AKIAIRNMBG7VZBPM2HXA"
AWS_SECRET_ACCESS_KEY = "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"

ADMIN_EMAILS = [
    "gagan_stage@mailinator.com",
    "inder_stage@mailinator.com",
    "brajesh_stage@mailinator.com",
]

PASSWORD_RESET_CONFIRM_URL = "reset-password/?uid={uid}&token={token}"
ACTIVATION_URL = "activate/?uid={uid}"

# Referral settings
DOMAIN = "stageroute.com"
APP_URL = "https://play.google.com/store/apps/details?id=com.stageroute"
INVITE_URL = "referral_code={referral_code}"
OTP_URL = "verify-phone/"
PINAX_REFERRALS_CODE_GENERATOR_CALLBACK = "users.utils.generate_code"

# Activity stream/feed/notifications/
ACTSTREAM_SETTINGS = {
    "MANAGER": "actstream.managers.ActionManager",
    "FETCH_RELATIONS": True,
}
MANAGERS = (("Author", "morsefactory@gmail.com"),)

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        # name of psql db on your running database server
        "NAME": "castjunction",
        "HOST": "localhost",  # assuming psql is running locally
        "PORT": 5432,
        # admin username that you set up with no password
        "USER": "postgres",
        "PASSWORD": "admin",
    }
}
# General
APPEND_SLASH = environ.Env(
    APPEND_SLASH=(bool, False),
)
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False
USE_L10N = True
USE_TZ = True
LOGIN_REDIRECT_URL = "/"

JOB_OPPORTUNITIES_URL = "jobs"
# Static Files
STATIC_ROOT = join(os.path.dirname(BASE_DIR), "staticfiles")
STATICFILES_DIRS = [
    join(os.path.dirname(BASE_DIR), "static"),
]
STATIC_URL = "/static/"
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# Media files
MEDIA_ROOT = str((root - 1)("media"))
MEDIA_URL = env("MEDIA_URL", default="/media/")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            "templates",
            os.path.join(BASE_DIR, "templates"),
            ACCOUNTS_TEMPLATE_DIR,
            OSCAR_MAIN_TEMPLATE_DIR,
        ],
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "django.core.context_processors.csrf",
                "django.core.context_processors.request",
                # 'postman.context_processors.inbox',
                # Oscar specific
                "oscar.apps.search.context_processors.search_form",
                "oscar.apps.promotions.context_processors.promotions",
                "oscar.apps.checkout.context_processors.checkout",
                "oscar.core.context_processors.metadata",
                "oscar.apps.customer.notifications.context_processors.notifications",
            ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                        "django.template.loaders.eggs.Loader",
                    ],
                ),
            ],
        },
    },
]

# Set DEBUG to False as a default for safety
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env("DEBUG")  # False if not in os.environ
ALLOWED_HOSTS = ["localhost"]
for config in TEMPLATES:
    config["OPTIONS"]["debug"] = DEBUG

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "simple": {"format": "%(levelname)s %(message)s"},
        "rq_console": {
            "format": "%(asctime)s %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "rq_console": {
            "level": "DEBUG",
            "class": "rq.utils.ColorizingStreamHandler",
            "formatter": "rq_console",
            "exclude": ["%(asctime)s"],
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "rq.worker": {"handlers": ["rq_console"], "level": "DEBUG"},
    },
}

# Custom user app
AUTH_USER_MODEL = "users.User"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
LOGIN_ON_EMAIL_CONFIRMATION = True
SOCIALACCOUNT_ADAPTER = "users.adapters.SocialAccountAdapter"
# Following config
# because of the same issue on this link:
# https://github.com/Tivix/django-rest-auth/issues/23#issuecomment-61416875
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_REQUIRED = False
SOCIALACCOUNT_QUERY_EMAIL = True

GRAPPELLI_AUTOCOMPLETE_SEARCH_FIELDS = {
    "cities": {
        "city": (
            "id__iexact",
            "name_std__icontains",
        )
    }
}

PINAX_LIKES_LIKABLE_MODELS = {
    "project.Job": {},  # can override default config settings for each model here
    "users.User": {},  # can override default config settings for each model here
}

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine",
        "URL": "http://127.0.0.1:9200/",
        "INDEX_NAME": "haystack",
    },
}

HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"
# refer section 4.9.5 of
# https://media.readthedocs.org/pdf/django-allauth/latest/django-allauth.pdf
SOCIALACCOUNT_PROVIDERS = {
    "facebook": {
        "METHOD": "oauth2",
        "SCOPE": ["email", "public_profile", "user_friends"],
        "FIELDS": [
            "id",
            "email",
            "name",
            "first_name",
            "last_name",
            "verified",
            "locale",
            "timezone",
            "link",
            "gender",
            "updated_time",
            "picture.height(1024).width(1024)",
        ],
        "AUTH_PARAMS": {"auth_type": "reauthenticate"},
        "EXCHANGE_TOKEN": True,
        "LOCALE_FUNC": lambda request: "en_US",
        "VERIFIED_EMAIL": False,
        "VERSION": "v2.6",
    }
}

# Django Rest Framework
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # 'rest_framework.authentication.SessionAuthentication',
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("rest_framework.filters.DjangoFilterBackend",),
}

PUSH_NOTIFICATIONS_SETTINGS = {
    "GCM_API_KEY": "AIzaSyC80ThMSSGsYmF8RC3mKB6wuwuEMRA6Itc",
    "APNS_CERTIFICATE": "/path/to/your/certificate.pem",
}

REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "users.serializers.RegisterSerializer"
}

REST_AUTH_SERIALIZERS = {
    "LOGIN_SERIALIZER": "users.serializers.LoginSerializer",
    "TOKEN_SERIALIZER": "users.serializers.TokenSerializer",
}

###########
# Payment #
###########
EBS_ACCOUNT_ID = 21276
EBS_SECRET_KEY = "3d55d0beca688c0cc199d514c01a4902"
EBS_CURRENCY = "INR"
EBS_MODE = "TEST"
EBS_CHANNEL = 0
EBS_PAGE_ID = 5553
EBS_RETURN_URL = "http://dev.stageroute.com/tokens/order/"
EBS_DEFAULT_CITY = "Mumbai"
EBS_DEFAULT_ADDRESS = "Default address"
EBS_DEFAULT_STATE = "Maharashtra"
EBS_DEFAULT_POSTALCODE = 400072
EBS_DEFAULT_COUNTRY = "IND"
EBS_DEFAULT_PHONE = 9899714165
EBS_DEFAULT_EMAIL = "gagan@morsefactory.com"

#######
# SMS #
#######
SMS_API_URL = "http://makemysms.in/api/sendsms.php/"
SMS_USERNAME = "StageRoute-T"
SMS_PASSWORD = "brajesh@123"
SMS_SENDER = "STROUT"
SMS_TYPE = 1

# OSCAR
OSCAR_DEFAULT_CURRENCY = "INR"
OSCARAPI_INITIAL_ORDER_STATUS = "Failed"

SITE_ID = 1
########
# CORS #
########
CORS_ALLOW_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")

CORS_ALLOW_HEADERS = (
    "x-requested-with",
    "content-type",
    "accept",
    "origin",
    "authorization",
    "x-csrftoken",
)
CORS_ORIGIN_ALLOW_ALL = True
