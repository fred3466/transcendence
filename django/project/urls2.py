from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('game/', include('game.urls')),
    path('', include('home.urls')),
    path('chat/', include('chat.urls')),
    path('users/', include('users.urls')),
    path('', include('security.urls')),
]

# to access user uploaded images (profile picture)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)