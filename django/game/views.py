from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_POST
from .models import Party, LeaderboardEntry, Tournament, TournamentMatch
from .forms import CreatePartyForm, CreateTournamentForm
from itertools import combinations
from django.db import transaction
import json, math, random

#fred
from dataclasses import dataclass
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from faker import Faker
from django_htmx.middleware import HtmxDetails
from django.core.paginator import Paginator
from django_htmx.http import HttpResponseClientRedirect,push_url

# Typing pattern recommended by django-stubs:
# https://github.com/typeddjango/django-stubs#how-can-i-create-a-httprequest-thats-guaranteed-to-have-an-authenticated-user
class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails
    
import logging
# logger = logging.getLogger(__name__)
logger = logging.getLogger("game")
#fred

@require_POST
@login_required(login_url='/users/login/')
def submit_game_result(request):
    logger.debug("== submit_game_result")
    try:
        data = json.loads(request.body)
        party_id = data.get('party_id')
        player_score = data.get('player_score')
        opponent_score = data.get('opponent_score')
        
        if not all([party_id, player_score is not None, opponent_score is not None]):
            return HttpResponseBadRequest("Missing required fields.")
        
        party = get_object_or_404(Party, id=party_id)
        
        # Create a new leaderboard entry
        LeaderboardEntry.objects.create(
            user=request.user,
            party=party,
            player_score=player_score,
            opponent_score=opponent_score
        )
        
        return JsonResponse({'status': 'success'})
    
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON.")


def create_matchups(tournament):
    logger.debug("== create_matchups")
    players = list(tournament.players.all())
    total_players = tournament.players.count()
    # If number of participants is not a power of 2, add byes
    next_power_of_two = 2 ** math.ceil(math.log2(total_players))
    byes = next_power_of_two - total_players
    # Shuffle participants for random matchups
    random.shuffle(players)
    # Add None as byes
    for _ in range(byes):
        players.append(None)
    # Create first round matchups
    for i in range(0, len(players), 2):
        player1 = players[i]
        player2 = players[i+1]
        if player1 and player2:
            TournamentMatch.objects.create(
                tournament=tournament,
                player1=player1,
                player2=player2,
                status='pending',
                round_number=1
            )
        elif player1 and not player2:
            # Handle bye: player1 automatically advances
            TournamentMatch.objects.create(
                tournament=tournament,
                player1=player1,
                player2=None,
                winner=player1,
                status='completed',
                round_number=1
            )


################################################################################
################################################################################
################################################################################
################################################################################


################################################################################
###     TOURNAMENT
################################################################################

@login_required(login_url='/users/login/')
def join_tournament(request: HtmxHttpRequest, tournament_id):
    logger.debug("== join_tournament tournament_id="+str(tournament_id))
    # template_name = "game/tournament_progress.html"
    # if request.htmx:
    #     template_name += "#my_htmx_content"
    tournament = get_object_or_404(Tournament, id=tournament_id)
    if tournament.status != 'waiting':
        return HttpResponseForbidden("Cannot join a tournament that is not active.")
    tournament.players.add(request.user)
    # return redirect('game:tournament_detail', tournament_id=tournament.id)
    # return push_url(redirect('game:tournament_progress', tournament_id=tournament.id),'')
    # return push_url(render('game:tournament_progress', {'tournament_id':tournament.id}),'')
    return tournament_progress(request,tournament.id)

@require_POST
@login_required(login_url='/users/login/')
def start_tournament(request: HtmxHttpRequest, tournament_id):
    logger.debug("== start_tournament")
    template_name = "game/tournament_progress.html"
    if request.htmx:
        template_name += "#my_htmx_content"
    tournament = get_object_or_404(Tournament, id=tournament_id)
    if tournament.creator != request.user:
        return HttpResponseForbidden("Only the creator can start the tournament.")
    if tournament.players.count() < 2:
        return HttpResponseBadRequest("Not enough participants to start the tournament.")

    with transaction.atomic():
        tournament.status = 'in_progress'
        tournament.save()
        create_matchups(tournament)  # Ensure this is a synchronous call

    matches = tournament.matches.all()  # assuming a related matches field

    # Add a participant check to each match
    for match in matches:
        match.is_participant = request.user == match.player1 or request.user == match.player2

    context = {
        'tournament_id': tournament.id,
        'tournament': tournament,
        'matches': matches,
    }
    return push_url(render(request, template_name, context),'')
    # return push_url(redirect('game:tournament_progress', tournament_id=tournament.id),'')
    # return redirect('game:tournament_progress', tournament_id=tournament.id)

@login_required(login_url='/users/login/')
def tournament_progress(request: HtmxHttpRequest, tournament_id):
    logger.debug("== tournament_progress")
    template_name = "game/tournament_progress.html"
    if request.htmx:
        template_name += "#my_htmx_content"
    tournament = get_object_or_404(Tournament, id=tournament_id)
    matches = tournament.matches.all()  # assuming a related matches field

    # Add a participant check to each match
    for match in matches:
        match.is_participant = request.user == match.player1 or request.user == match.player2

    context = {
        'tournament': tournament,
        'matches': matches,
    }
    return push_url(render(request, template_name, context),'')

@login_required(login_url='/users/login/')
def tournament_detail(request: HtmxHttpRequest, tournament_id):
    logger.debug("== tournament_detail")
    template_name = "game/tournament_detail.html"
    if request.htmx:
    	template_name += "#my_htmx_content"
    tournament = get_object_or_404(Tournament, id=tournament_id)
    is_creator = tournament.creator == request.user
    can_start = is_creator and tournament.players.count() >= 2 and tournament.status == 'waiting'
    return push_url(render(request, template_name, {
        'tournament': tournament,
        'is_creator': is_creator,
        'can_start': can_start,
    }),'')

@login_required(login_url='/users/login/')
def tournament_list(request: HtmxHttpRequest) -> HttpResponse:
    logger.debug("== tournament_list")
    template_name = "game/tournament_list.html"
    if request.htmx:
    	template_name += "#my_htmx_content"
    
    if request.method == 'POST':
        create_tournament_form = CreateTournamentForm(request.POST)
        if create_tournament_form.is_valid():
            tournament = create_tournament_form.save(commit=False)
            tournament.creator = request.user
            tournament.save()
            tournament.players.add(request.user)
            logger.debug("== tournament_list tournament saved")
            # response= redirect('game:tournament_detail', tournament_id=tournament.id)
    # else:
    create_tournament_form = CreateTournamentForm()

    tournaments = Tournament.objects.all().order_by('id').reverse()

    response= render(request, template_name, {
        'create_tournament_form': create_tournament_form,
        'tournaments': tournaments,
    })
    return push_url(response,'')   

# @login_required(login_url='/users/login/')
# def play_match(request: HtmxHttpRequest, tournament_id, match_id):
#     logger.debug("== play_match")
#     template_name = "game/game.html"
#     if request.htmx:
#         template_name += "#my_htmx_content"
#     matche = get_object_or_404(TournamentMatch, id=match_id, tournament_id=tournament_id)
#     if matche.status != 'pending':
#         return HttpResponseBadRequest("Match already in progress or completed.")
#     if request.user not in [matche.player1, matche.player2]:
#         return HttpResponseForbidden("You are not a participant in this match.")
#
#     if matche.party:
#         party = matche.party
#     else:
#         # Create a new Party for the matche
#         party = Party.objects.create(
#             creator=request.user,
#             num_players=2,
#             status='active'
#         )
#         # Add both players to the Party
#         party.participants.add(matche.player1, matche.player2)
#         # Associate the party with the matche
#         matche.party = party
#         matche.save()
#
#     logger.debug("== play_match party_id="+str(party.id)+" match_id="+str(match_id))
#     response= render(request, template_name, {
#         'party_id': party.id,
#         'match_id': matche.id,
#         # 'tournament_id': matche.tournament.id,
#     })
#     return push_url(response,'')
#     # return redirect('game:game_with_match', party_id=party.id, match_id=matche.id,)
# # path('tournaments/<int:tournament_id>/play_match/<int:match_id>/', play_match, name='play_match'),

@login_required(login_url='/users/login/')
def play_match(request, tournament_id, match_id):
    logger.debug("== play_match")
    match = get_object_or_404(TournamentMatch, id=match_id, tournament_id=tournament_id)
    if match.status != 'pending':
        return HttpResponseBadRequest("Match already in progress or completed.")
    if request.user not in [match.player1, match.player2]:
        return HttpResponseForbidden("You are not a participant in this match.")

    if match.party:
        party = match.party
    else:
        # Create a new Party for the match
        party = Party.objects.create(
            creator=request.user,
            num_players=2,
            status='active'
        )
        # Add both players to the Party
        party.participants.add(match.player1, match.player2)
        # Associate the party with the match
        match.party = party
        match.save()

    return redirect('game:game_with_match', party_id=party.id, match_id=match.id,)


################################################################################
###     GAME
################################################################################

def game(request: HtmxHttpRequest, party_id, match_id=None) -> HttpResponse:
    logger.debug("== game")
    party = get_object_or_404(Party, id=party_id)
    tournament_id = None
    if match_id:
        match = get_object_or_404(TournamentMatch, id=match_id)
        tournament_id = match.tournament.id

    template_name = "game/game.html"
    if request.htmx:
        template_name += "#my_htmx_content"
    return render(request, template_name, {
        'party_id': party_id,
        'match_id': match_id,
        'tournament_id': tournament_id,
        'user': request.user,
        'num_players': party.num_players,
        'show_alerts': False,
    })


# def game(request: HtmxHttpRequest, party_id, match_id=None) -> HttpResponse:
#     logger.debug("== game")
#     party = get_object_or_404(Party, id=party_id)
#     tournament_id = None
#     if match_id:
#         matche = get_object_or_404(TournamentMatch, id=match_id)
#         tournament_id = matche.tournament.id
#
#     template_name = "game/game.html"
#     if request.htmx:
#         template_name += "#my_htmx_content"
#     response= render(request, template_name, {
#         'party_id': party_id,
#         'match_id': match_id,
#         'tournament_id': tournament_id,
#         'user': request.user,
#         'num_players': party.num_players,
#         'show_alerts': False,
#     })
#     return push_url(response,f"")  

# @login_required(login_url='/users/login/')
# def lobby(request: HtmxHttpRequest) -> HttpResponse:
#     logger.debug("== lobby")
#     if request.method == 'POST':
#         form = CreatePartyForm(request.POST)
#         try:
#             # Convert num_players to an integer
#             num_players = int(request.POST.get('num_players', 0))  # Default to 0 if not provided
#         except ValueError:
#             num_players = 0  # Handle invalid input
#
#         # Check if num_players is 1, otherwise proceed with form validation
#         if num_players == 1:
#             template_name = "game/game.html"
#             if request.htmx:
#                 template_name += "#my_htmx_content"
#             return render(request, template_name, {
#                 'party_id': None,
#                 'match_id': None,
#                 'tournament_id': None,
#                 'user': request.user,
#                 'num_players': 1,
#                 'show_alerts': False,
#             })
#         # Vérifier si num_players est 0 (jeu local)
#         elif num_players == 0:
#             template_name = "game/game.html"
#             if request.htmx:
#                 template_name += "#my_htmx_content"
#                 return render(request, template_name, {
#                 'party_id': None,
#                 'match_id': None,
#                 'tournament_id': None,
#                 'user': request.user,
#                 'num_players': 0,
#                 'show_alerts': False,
#             })
#
#         # If the form is valid, save the party
#         if form.is_valid():
#             party = form.save(commit=False)
#             party.creator = request.user
#             party.save()
# #################### copié depuis game:game, à revoir  
#             tournament_id = None
#             #if match_id:
#              #   match = get_object_or_404(TournamentMatch, id=match_id)
#             #    tournament_id = match.tournament.id
#             template_name = "game/game.html"
#             if request.htmx:
#                 template_name += "#my_htmx_content"
#             return render(request, template_name, {
#                 'show_alerts' : False,
#                 'party_id': party.id,
#                 #'match_id': match_id,
#                 #'tournament_id': tournament_id,
#                 'user': request.user,
#                 'num_players': party.num_players,
#                 'show_alerts': False,
#             })
#             #return redirect('game:game', party_id=party.id)  # Redirect to the game
#             ##return HttpResponseClientRedirect('game/game.html', party_id=party.id)  # Redirect to the game
#             ##return render(request,'game/game.html', {'party_id' : party.id})  # Redirect to the game
# ########################################            
#     else:
#         form = CreatePartyForm()
#
#     # Handle GET request
#     template_name = "game/lobby.html"
#     if request.htmx:
#         template_name += "#my_htmx_content"
#
#     parties = Party.objects.exclude(status='completed').order_by('id').reverse()
#     return render(request, template_name, {
#         'show_alerts': False,
#         'form': form,
#         'parties': parties,
#         'num_players': None  # Default to None for GET request
#     })


@login_required(login_url='/users/login/')
def lobby(request: HtmxHttpRequest) -> HttpResponse:
    logger.debug("== lobby")
    if request.method == 'POST':
        form = CreatePartyForm(request.POST)
        try:
            # Convert num_players to an integer
            num_players = int(request.POST.get('num_players', 0))  # Default to 0 if not provided
        except ValueError:
            num_players = 0  # Handle invalid input

        logger.debug("== lobby num_players="+str(num_players))
        # Check if num_players is 1, otherwise proceed with form validation
        if num_players == 1:
            template_name = "game/game.html"
            if request.htmx:
                template_name += "#my_htmx_content"
            response= render(request, template_name, {
                'party_id': None,
                'match_id': None,
                'tournament_id': None,
                'user': request.user,
                'num_players': 1,
                'show_alerts': False,
            })
            return push_url(response,'')   
        # Vérifier si num_players est 0 (jeu local)
        elif num_players == 0:
            template_name = "game/game.html"
            if request.htmx:
                template_name += "#my_htmx_content"
                response= render(request, template_name, {
                'party_id': None,
                'match_id': None,
                'tournament_id': None,
                'user': request.user,
                'num_players': 0,
                'show_alerts': False,
            })
            return push_url(response,f"/game/lobby/")   

        # If the form is valid, save the party
        if form.is_valid():
            party = form.save(commit=False)
            party.creator = request.user
            party.save()
#################### copié depuis game:game, à revoir  
            tournament_id = None
            #if match_id:
             #   match = get_object_or_404(TournamentMatch, id=match_id)
            #    tournament_id = match.tournament.id
            template_name = "game/game.html"
            if request.htmx:
                template_name += "#my_htmx_content"
            response= render(request, template_name, {
                'party_id': party.id,
                #'match_id': match_id,
                #'tournament_id': tournament_id,
                'user': request.user,
                'num_players': party.num_players,
                'show_alerts': False,
            })
            return push_url(response,f"/game/lobby/")   
            #return redirect('game:game', party_id=party.id)  # Redirect to the game
            ##return HttpResponseClientRedirect('game/game.html', party_id=party.id)  # Redirect to the game
            ##return render(request,'game/game.html', {'party_id' : party.id})  # Redirect to the game
########################################            
    else:
        form = CreatePartyForm()

    # Handle GET request
    template_name = "game/lobby.html"
    if request.htmx:
        template_name += "#my_htmx_content"
    parties = Party.objects.exclude(status='completed').order_by('id').reverse()
    response=render(request, template_name, {
        'show_alerts': False,
        'form': form,
        'parties': parties,
        'num_players': None  # Default to None for GET request
    })
    return push_url(response,f"/game/lobby/")   


################################################################################
################################################################################
################################################################################
################################################################################
@dataclass
class Person:
    id: int
    name: str


faker = Faker()
people = [Person(id=i, name=faker.name()) for i in range(1, 235)]

@require_GET
def partial_rendering(request: HtmxHttpRequest) -> HttpResponse:
    logger.debug("== partial_rendering")
    # Standard Django pagination
    page_num = request.GET.get("page", "1")
    page = Paginator(object_list=people, per_page=10).get_page(page_num)

    # The htmx magic - render just the `#table-section` partial for htmx
    # requests, allowing us to skip rendering the unchanging parts of the
    # template.
    template_name = "partial-rendering.html"
    if request.htmx:
        template_name += "#table-section"

    return render(
        request,
        template_name,
        {
            "page": page,
        },
    )