import os

# Default to local settings if not specified
env_setting = os.getenv('DJANGO_SETTINGS_MODULE', 'optiexam.settings.local')
if 'production' in env_setting:
    from .production import *
else:
    from .local import *
