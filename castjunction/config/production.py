"""Prodcution settings."""
from .common import *

# Production settings for castjunction.

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
# https://devcenter.heroku.com/articles/getting-started-with-django
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# Media files
MEDIA_URL = env("MEDIA_URL", default="http://api.stageroute.com/media/")

INSTALLED_APPS = INSTALLED_APPS
# django-secure
# http://django-secure.readthedocs.org/en/v0.1.2/settings.html
INSTALLED_APPS += ("djangosecure",)

SECRET_KEY = ")3fa+@b7lbe$35ixds!3+xeo_@jy+p4qb%rw%7!ywnlg88aq57"

DATABASES = {"default": env.db("DATABASE_URL")}

ADMIN_EMAILS = [
    "gagan@morsefactory.com",
    "inder@morsefactory.com",
    "brajesh@morsefactory.com",
]
# SECURE_HSTS_SECONDS = 60
# SECURE_HSTS_INCLUDE_SUBDOMAINS = values.BooleanValue(True)
# SECURE_FRAME_DENY = values.BooleanValue(True)
# SECURE_CONTENT_TYPE_NOSNIFF = values.BooleanValue(True)
# SECURE_BROWSER_XSS_FILTER = values.BooleanValue(True)
# SESSION_COOKIE_SECURE = values.BooleanValue(False)
# SESSION_COOKIE_HTTPONLY = values.BooleanValue(True)
# SECURE_SSL_REDIRECT = values.BooleanValue(False)

# Site
# https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ("gunicorn",)

# Template
# https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
TEMPLATE_LOADERS = (
    (
        "django.template.loaders.cached.Loader",
        (
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ),
    ),
)

# Media files
# http://django-storages.readthedocs.org/en/latest/index.html
# INSTALLED_APPS += ('storages',)
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
# AWS_ACCESS_KEY_ID = values.Value('DJANGO_AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = values.Value('DJANGO_AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = values.Value('DJANGO_AWS_STORAGE_BUCKET_NAME')
# AWS_AUTO_CREATE_BUCKET = True
# AWS_QUERYSTRING_AUTH = False
# MEDIA_URL = 'https://s3.amazonaws.com/{}/'.format(AWS_STORAGE_BUCKET_NAME)
# AWS_S3_CALLING_FORMAT = OrdinaryCallingFormat()

# https://developers.google.com/web/fundamentals/performance/optimizing-content-efficiency/http-caching#cache-control
# Response can be cached by browser and any intermediary caches (i.e. it is "public") for up to 1 day
# 86400 = (60 seconds x 60 minutes x 24 hours)
# AWS_HEADERS = {
#     'Cache-Control': 'max-age=86400, s-maxage=86400, must-revalidate',
# }

# Static files
# STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

###########
# Payment #
###########
EBS_ACCOUNT_ID = 21276
EBS_SECRET_KEY = "3d55d0beca688c0cc199d514c01a4902"
EBS_CURRENCY = "INR"
EBS_MODE = "LIVE"
EBS_CHANNEL = 0
EBS_PAGE_ID = 5553
EBS_RETURN_URL = "http://api.stageroute.com/tokens/order/"
EBS_DEFAULT_CITY = "Mumbai"
EBS_DEFAULT_ADDRESS = "Plot no 111 Flat no 7 Shere Punjab Society Mahakali Caves Road Andheri East Mumbai 400093"
EBS_DEFAULT_STATE = "Maharashtra"
EBS_DEFAULT_POSTALCODE = 400093
EBS_DEFAULT_COUNTRY = "IND"
EBS_DEFAULT_PHONE = 9923694541
EBS_DEFAULT_EMAIL = "morsefactory@gmail.com"


# Caching
redis_url = env("REDIS_URL", default="redis://localhost:6379")
CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": redis_url,
        "OPTIONS": {
            "DB": 0,
            "PASSWORD": None,
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": 50,
                "timeout": 20,
            },
        },
    }
}

# Django RQ production settings
RQ_QUEUES = {
    "default": {
        "HOST": "localhost",
        "PORT": 6379,
        "DB": 0,
        "DEFAULT_TIMEOUT": 360,
    },
    "high": {
        "URL": env("REDIS_URL", default="redis://localhost:6379/0"),
        "DEFAULT_TIMEOUT": 500,
    },
    "low": {
        "HOST": "localhost",
        "PORT": 6379,
        "DB": 0,
    },
}
