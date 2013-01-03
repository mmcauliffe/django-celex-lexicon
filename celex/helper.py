import os

from django.conf import settings

def fetch_celex_resource(uri):
    path = os.path.join(settings.CELEX_ROOT,uri)
    return path

def fetch_media_resource(uri):
    path = os.path.join(settings.MEDIA_ROOT,uri)
    return path
