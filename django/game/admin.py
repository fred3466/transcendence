# game/admin.py

from django.contrib import admin
from .models import Party, LeaderboardEntry

admin.site.register(Party)
admin.site.register(LeaderboardEntry)
