from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
	re_path(r'ws/pong/(?P<party_id>\d+)/(?P<match_id>\d+)/$', consumers.PongConsumer.as_asgi()),
    re_path(r'ws/pong/(?P<party_id>\w+)/$', consumers.PongConsumer.as_asgi()),
]
