from django.urls import path
from .views import game, lobby, submit_game_result, join_tournament, tournament_detail, start_tournament, tournament_list, tournament_progress, play_match
from django.conf.urls.static import static
from django.conf import settings

app_name = 'game'

urlpatterns = [
	path('<int:party_id>/play_match/<int:match_id>/', game, name='game_with_match'),  # Game page with party ID and match ID
    path('<int:party_id>/', game, name='game'),  # Game page with party ID
    path('lobby/', lobby, name='lobby'),  # Lobby page
    path('submit_result/', submit_game_result, name='submit_game_result'),  # New endpoint
	
    # Tournament URLs
    path('tournaments/', tournament_list, name='tournament_list'),
    path('tournaments/<int:tournament_id>/', tournament_detail, name='tournament_detail'),
	path('tournaments/<int:tournament_id>/progress/', tournament_progress, name='tournament_progress'),
    path('tournaments/<int:tournament_id>/join/', join_tournament, name='join_tournament'),
    path('tournaments/<int:tournament_id>/start/', start_tournament, name='start_tournament'),
	path('tournaments/<int:tournament_id>/play_match/<int:match_id>/', play_match, name='play_match'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
