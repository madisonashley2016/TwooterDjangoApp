from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    path('ws/message/<pk>/', consumers.MessageConsumer),
    path('ws/', consumers.ButtonConsumer),
    path('ws/latest/', consumers.ButtonConsumer),
    path('ws/explore/', consumers.ButtonConsumer),
    path('ws/explore/latest/', consumers.ButtonConsumer),
    path('ws/explore/tags/', consumers.ButtonConsumer),
    path('ws/profile/<username>/', consumers.ButtonConsumer),
    path('ws/profile/<username>/replies/', consumers.ButtonConsumer),
    path('ws/profile/<username>/likes/', consumers.ButtonConsumer),
    path('ws/twoots/<pk>/', consumers.ButtonConsumer),
    path('ws/twoot/', consumers.ButtonConsumer),
    path('ws/comment/<pk>/', consumers.ButtonConsumer),
]