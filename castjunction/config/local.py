"""local settings."""
import os
from .common import *

for config in TEMPLATES:
    config['OPTIONS']['debug'] = DEBUG

# Testing
INSTALLED_APPS = INSTALLED_APPS
INSTALLED_APPS += ('django_nose', 'silk')
MIDDLEWARE_CLASSES += ('silk.middleware.SilkyMiddleware',)
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    BASE_DIR,
    '--nologcapture',
    '--with-coverage',
    '--with-progressive',
    '--cover-package={}'.format(BASE_DIR)
]


# Django RQ local settings
RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },
    'high': {
        'URL': os.getenv('REDISTOGO_URL', 'redis://localhost:6379/0'),
        'DEFAULT_TIMEOUT': 500,
    },
    'low': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
    }
}

DATABASES = {
    'default': env.db('DATABASE_URL', 'postgis://postgres:admin@localhost:5432/castjunction'),
}
