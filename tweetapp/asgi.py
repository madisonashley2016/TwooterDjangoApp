"""
ASGI config for tweetapp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

#from django.core.asgi import get_asgi_application
import django #added 
from channels.routing import get_default_application #added for deployment

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tweetapp.settings')
os.environ['ASGI_THREADS']="4" #added.

django.setup() #added

#application = get_asgi_application()
application = get_default_application()