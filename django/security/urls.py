from django.urls import path
from security.views import vulnerable_view, script_view, script_2_view, csrf_view

app_name = 'security'

urlpatterns = [
	path('vulnerable/', vulnerable_view, name='vulnerable'),
	path('script/', script_view, name='script'),
	path('script_2/', script_2_view, name='script_2'),
	path('csrf/', csrf_view, name='csrf'),
]