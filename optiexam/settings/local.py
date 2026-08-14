from .base import *

# Local / Offline Standalone Settings
DEBUG = env.bool('DEBUG', default=True)

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
