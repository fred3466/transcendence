# game/consumers.py

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import Party, LeaderboardEntry, Tournament, TournamentMatch
from django.db.models import Max
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class PongConsumer(AsyncWebsocketConsumer):
    ball_radius = 10
    paddle_width = 10
    paddle_height = 100
    game_loop_task = None

    game_states = {}

    @database_sync_to_async
    def get_username(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            return user.username
        except User.DoesNotExist:
            return 'Unknown User'

    async def connect(self):
        self.party_id = self.scope['url_route']['kwargs']['party_id']
        self.match_id = self.scope['url_route']['kwargs'].get('match_id', None)
        self.room_group_name = f'pong_{self.party_id}'
        self.game_loop_task = None
        self.user_id = self.scope['user'].id if self.scope['user'].is_authenticated else None

        # Get the party's num_players
        self.num_players = await self.get_party_num_players(self.party_id)
        if self.num_players is None:
            await self.close()
            return

        # Associate the party with the match if match_id is present
        if self.match_id:
            await self.associate_party_with_match(self.party_id, self.match_id)

        # Join the group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Update party player count
        await self.update_party_on_connect(self.party_id)

        # Initialize game state
        if self.room_group_name not in PongConsumer.game_states:
            PongConsumer.game_states[self.room_group_name] = {
                'players': [],
                'paddle_positions': {},  # Map user_id to paddle info
                'scores': {},
                'ball': {
                    'x': 400,
                    'y': 300,
                    'speed_x': 5,
                    'speed_y': 5,
                },
                'game_started': False,
                'num_players': self.num_players,
                'game_loop_started': False,
            }

        game_state = PongConsumer.game_states[self.room_group_name]

        # Add player to the game
        if self.user_id not in game_state['players'] and len(game_state['players']) < game_state['num_players']:
            game_state['players'].append(self.user_id)
            # Initialize paddle positions based on player number
            if len(game_state['players']) == 1:
                # Player 1: Left paddle
                paddle = {
                    'x': 0,
                    'y': (600 - self.paddle_height) / 2,
                    'width': self.paddle_width,
                    'height': self.paddle_height,
                    'orientation': 'vertical',
                }
            elif len(game_state['players']) == 2:
                # Player 2: Right paddle
                paddle = {
                    'x': 800 - self.paddle_width,
                    'y': (600 - self.paddle_height) / 2,
                    'width': self.paddle_width,
                    'height': self.paddle_height,
                    'orientation': 'vertical',
                }
            elif len(game_state['players']) == 3 and game_state['num_players'] == 3:
                # Player 3: Top paddle
                paddle = {
                    'x': (800 - self.paddle_height) / 2,
                    'y': 0,
                    'width': self.paddle_height,  # Swap width and height
                    'height': self.paddle_width,
                    'orientation': 'horizontal',
                }
            game_state['paddle_positions'][self.user_id] = paddle
            game_state['scores'][self.user_id] = 0

        # Send user ID to the client
        await self.send(text_data=json.dumps({
            'action': 'set_user_id',
            'user_id': self.user_id,
        }))

        # Start game if enough players have joined
        if len(game_state['players']) == game_state['num_players'] and not game_state['game_started']:
            game_state['game_started'] = True

            # Retrieve usernames
            player_usernames = {}
            for player_id in game_state['players']:
                username = await self.get_username(player_id)
                player_usernames[player_id] = username

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'start_game',
                    'player_ids': game_state['players'],
                    'player_usernames': player_usernames,
                    'countdown_duration': 3,
                }
            )
            if not game_state['game_loop_started']:
                game_state['game_loop_started'] = True
                asyncio.create_task(self.start_game_loop_with_delay(countdown_duration=3))

    async def start_game_loop_with_delay(self, countdown_duration):
        await asyncio.sleep(countdown_duration + 0.5)  # Wait for countdown + 'GO!' display time
        self.game_loop_task = asyncio.create_task(self.game_loop())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # Remove player from game state
        try:
            game_state = PongConsumer.game_states[self.room_group_name]
            if self.user_id in game_state.get('players', []):
                game_state['players'].remove(self.user_id)
                game_state['paddle_positions'].pop(self.user_id, None)
                game_state['scores'].pop(self.user_id, None)
            if not game_state.get('players'):
                del PongConsumer.game_states[self.room_group_name]
        except KeyError:
            pass

        # Update party info
        await self.update_party_on_disconnect(self.party_id)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'move_paddle':
            game_state = PongConsumer.game_states[self.room_group_name]
            paddle = game_state['paddle_positions'][self.user_id]
            # Update paddle position based on orientation
            if 'paddleY' in data:
                paddle['y'] = data['paddleY']
            if 'paddleX' in data:
                paddle['x'] = data['paddleX']

    async def start_game(self, event):
        await self.send(text_data=json.dumps({
            'action': 'start_game',
            'player_ids': event['player_ids'],
            'player_usernames': event['player_usernames'],
            'countdown_duration': event.get('countdown_duration', 3),
        }))

    def increase_ball_speed(self, speed_x, speed_y, max_speed, speed_increment):
        # Increase speed while keeping the direction
        new_speed_x = speed_x * speed_increment
        new_speed_y = speed_y * speed_increment

        # Cap the speeds to the maximum allowed speed
        if abs(new_speed_x) > max_speed:
            new_speed_x = max_speed if new_speed_x > 0 else -max_speed
        if abs(new_speed_y) > max_speed:
            new_speed_y = max_speed if new_speed_y > 0 else -max_speed

        return new_speed_x, new_speed_y

    async def game_loop(self):
        game_state = PongConsumer.game_states[self.room_group_name]
        ball = game_state['ball']
        paddle_positions = game_state['paddle_positions']
        players = game_state['players']
        scores = game_state['scores']
        num_players = game_state['num_players']

        # Define the maximum speed and speed increment
        max_speed = 15  # Maximum speed the ball can reach
        speed_increment = 1.1  # Speed multiplier on each paddle hit

        while True:
            # Update ball position
            ball['x'] += ball['speed_x']
            ball['y'] += ball['speed_y']

            # Collision with walls
            if ball['x'] - self.ball_radius <= 0:
                # Left boundary
                if num_players == 2:
                    scores[players[1]] += 1
                else:
                    scores[players[0]] -= 1
                await self.reset_ball()
                continue
            elif ball['x'] + self.ball_radius >= 800:
                # Right boundary
                if num_players == 2:
                    scores[players[0]] += 1
                else:
                    scores[players[1]] -= 1
                await self.reset_ball()
                continue

            # For 3-player games, check top boundary
            if num_players == 3:
                if ball['y'] - self.ball_radius <= 0:
                    # Top boundary (Player 3 missed)
                    scores[players[2]] -= 1
                    await self.reset_ball()
                    continue
                elif ball['y'] + self.ball_radius >= 600:
                    # Bottom wall collision (bounce back)
                    ball['y'] = 600 - self.ball_radius
                    ball['speed_y'] *= -1
            else:
                # For 2-player games, bounce off top and bottom walls
                if ball['y'] - self.ball_radius <= 0:
                    ball['y'] = self.ball_radius
                    ball['speed_y'] *= -1
                elif ball['y'] + self.ball_radius >= 600:
                    ball['y'] = 600 - self.ball_radius
                    ball['speed_y'] *= -1

            # Check for game over condition
            if num_players == 2:
                for player_id, score in scores.items():
                    if score >= 5:
                        await self.end_game(winner=player_id)
                        return
            else:
                for player_id, score in scores.items():
                    if score <= -5:
                        await self.end_game(loser=player_id)
                        return

            # Collision with paddles
            for player_id in players:
                paddle = paddle_positions[player_id]
                if self.check_ball_paddle_collision(ball, paddle):
                    if paddle['orientation'] == 'vertical':
                        # Reverse speed_x
                        ball['speed_x'] *= -1
                        # Adjust ball's x position to prevent sticking
                        if ball['x'] < 400:
                            # Left paddle
                            ball['x'] = paddle['x'] + paddle['width'] + self.ball_radius
                        else:
                            # Right paddle
                            ball['x'] = paddle['x'] - self.ball_radius
                    elif paddle['orientation'] == 'horizontal' and num_players == 3:
                        # Reverse speed_y
                        ball['speed_y'] *= -1
                        # Adjust ball's y position to prevent sticking
                        ball['y'] = paddle['y'] + paddle['height'] + self.ball_radius
                    # Increase ball speed
                    ball['speed_x'], ball['speed_y'] = self.increase_ball_speed(
                        ball['speed_x'], ball['speed_y'], max_speed, speed_increment
                    )

            # Broadcast the game state to all players
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'update_state',
                    'ballX': ball['x'],
                    'ballY': ball['y'],
                    'paddles': paddle_positions,
                    'scores': scores,
                }
            )

            await asyncio.sleep(0.016)

    def check_ball_paddle_collision(self, ball, paddle):
        if paddle['orientation'] == 'vertical':
            # Vertical paddle collision detection
            if (
                ball['x'] - self.ball_radius <= paddle['x'] + paddle['width'] and
                ball['x'] + self.ball_radius >= paddle['x'] and
                ball['y'] + self.ball_radius >= paddle['y'] and
                ball['y'] - self.ball_radius <= paddle['y'] + paddle['height']
            ):
                return True
        elif paddle['orientation'] == 'horizontal':
            # Horizontal paddle collision detection
            if (
                ball['y'] - self.ball_radius <= paddle['y'] + paddle['height'] and
                ball['y'] + self.ball_radius >= paddle['y'] and
                ball['x'] + self.ball_radius >= paddle['x'] and
                ball['x'] - self.ball_radius <= paddle['x'] + paddle['width']
            ):
                return True
        return False

    async def reset_ball(self):
        # Reset the ball to the center
        game_state = PongConsumer.game_states[self.room_group_name]
        ball = game_state['ball']
        ball['x'] = 400
        ball['y'] = 300

        # Reset ball speed to initial values
        initial_speed_x = 5
        initial_speed_y = 5

        # Randomize initial direction
        ball['speed_x'] = initial_speed_x if ball['speed_x'] < 0 else -initial_speed_x
        ball['speed_y'] = initial_speed_y

        # Brief pause before resuming
        await asyncio.sleep(1)

    async def update_state(self, event):
        await self.send(text_data=json.dumps({
            'action': 'update_state',
            'ballX': event['ballX'],
            'ballY': event['ballY'],
            'paddles': event['paddles'],
            'scores': event['scores'],
        }))

    async def end_game(self, loser=None, winner=None):
        game_state = PongConsumer.game_states[self.room_group_name]
        num_players = game_state['num_players']
        if winner is not None:
            # For 2-player game
            losers = [pid for pid in game_state['players'] if pid != winner]
            winners = [winner]
        elif loser is not None:
            # For 3-player game
            winners = [pid for pid in game_state['players'] if pid != loser]
            losers = [loser]
        else:
            # Should not happen
            return

        # Notify players about the game result
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_over',
                'winners': winners,
                'losers': losers,
                'scores': game_state['scores'],
            }
        )
        # Update user profiles
        await self.update_user_profiles(winners, losers)

        # Create LeaderboardEntry for 2-player games
        if num_players == 2:
            await self.create_leaderboard_entry(game_state['players'], game_state['scores'])

        # Tournament match handling
        if self.match_id:
            await self.update_tournament_match(self.match_id, winner, game_state['scores'])

        # Cancel the game loop task if it's still running
        if self.game_loop_task and not self.game_loop_task.done():
            self.game_loop_task.cancel()
            try:
                await self.game_loop_task
            except asyncio.CancelledError:
                pass

        # Clean up game state
        del PongConsumer.game_states[self.room_group_name]

        # Remove all users from the group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Set party status to 'completed'
        await self.set_party_completed(self.party_id)


    async def game_over(self, event):
        winners = event['winners']
        losers = event['losers']
        scores = event['scores']
        if self.user_id in winners:
            message = 'You win!'
        else:
            message = 'You lose!'
        await self.send(text_data=json.dumps({
            'action': 'game_over',
            'message': message,
            'scores': scores,
        }))

    async def create_leaderboard_entry(self, players, scores):
        # Extract player IDs
        player1_id = players[0]
        player2_id = players[1]
        player1_score = scores[player1_id]
        player2_score = scores[player2_id]

        # Get the party instance
        party = await database_sync_to_async(Party.objects.get)(id=self.party_id)

        # Create LeaderboardEntry for player1
        await database_sync_to_async(LeaderboardEntry.objects.create)(
            user_id=player1_id,
            opponent_id=player2_id,
            party=party,
            player_score=player1_score,
            opponent_score=player2_score
        )

        # Create LeaderboardEntry for player2
        await database_sync_to_async(LeaderboardEntry.objects.create)(
            user_id=player2_id,
            opponent_id=player1_id,
            party=party,
            player_score=player2_score,
            opponent_score=player1_score
        )

    @database_sync_to_async
    def get_party_num_players(self, party_id):
        try:
            party = Party.objects.get(id=party_id)
            return party.num_players
        except Party.DoesNotExist:
            return None

    @database_sync_to_async
    def update_party_on_connect(self, party_id):
        try:
            party = Party.objects.get(id=party_id)
            party.nbPlayer += 1
            if party.nbPlayer >= party.num_players:
                party.status = 'in_progress'
            party.save()
        except Party.DoesNotExist:
            pass

    @database_sync_to_async
    def update_party_on_disconnect(self, party_id):
        try:
            party = Party.objects.get(id=party_id)
            if party.status != 'completed':
                party.nbPlayer -= 1
                if party.nbPlayer <= 0:
                    party.status = 'active'
                party.save()
        except Party.DoesNotExist:
            pass

    @database_sync_to_async
    def set_party_completed(self, party_id):
        try:
            party = Party.objects.get(id=party_id)
            party.status = 'completed'
            party.save()
        except Party.DoesNotExist:
            pass

    async def update_user_profiles(self, winners, losers):
        for user_id in winners:
            try:
                user = await database_sync_to_async(User.objects.get)(id=user_id)
                profile = await database_sync_to_async(lambda: user.profile)()
                profile.wins += 1
                await database_sync_to_async(profile.save)()
            except User.DoesNotExist:
                pass
        for user_id in losers:
            try:
                user = await database_sync_to_async(User.objects.get)(id=user_id)
                profile = await database_sync_to_async(lambda: user.profile)()
                profile.losses += 1
                await database_sync_to_async(profile.save)()
            except User.DoesNotExist:
                pass

    async def update_tournament_match(self, match_id, winner, scores):
        try:
            logger.debug(f"Updating tournament match {match_id} with winner {winner}")
            match = await database_sync_to_async(TournamentMatch.objects.get)(id=match_id)
            winner_user = await database_sync_to_async(User.objects.get)(id=winner)
            match.winner = winner_user
            match.status = 'completed'
            await database_sync_to_async(match.save)()

            # Properly retrieve the tournament instance
            tournament = await database_sync_to_async(Tournament.objects.get)(id=match.tournament_id)
            await self.progress_tournament(tournament)
        except TournamentMatch.DoesNotExist:
            logger.error(f"TournamentMatch with id {match_id} does not exist.")
        except User.DoesNotExist:
            logger.error(f"User with id {winner} does not exist.")
        except Exception as e:
            logger.error(f"Error updating tournament match: {e}")

    async def progress_tournament(self, tournament):
        logger.debug(f"Progressing tournament {tournament.id}")
        
        # Get the current round number
        current_round = await database_sync_to_async(
            lambda: tournament.matches.aggregate(Max('round_number'))['round_number__max']
        )()
        logger.debug(f"Current round: {current_round}")
        
        # Check if all matches in the current round are completed
        total_matches_in_current_round = await database_sync_to_async(
            lambda: tournament.matches.filter(round_number=current_round).count()
        )()
        completed_matches_in_current_round = await database_sync_to_async(
            lambda: tournament.matches.filter(round_number=current_round, status='completed').count()
        )()
        logger.debug(f"Total matches: {total_matches_in_current_round}, Completed matches: {completed_matches_in_current_round}")
        
        if completed_matches_in_current_round < total_matches_in_current_round:
            logger.debug("Not all matches in the current round are completed.")
            return  # Not all matches completed yet

        # Get all winners from the completed matches in the current round
        winners_data = await database_sync_to_async(
            lambda: list(
                tournament.matches.filter(round_number=current_round, status='completed')
                .exclude(winner__isnull=True)
                .values('winner_id', 'winner__username')
            )
        )()
        logger.debug(f"Winners data: {winners_data}")
        
        # Now build list of winner User objects
        winners = []
        for data in winners_data:
            winner_id = data['winner_id']
            winner_username = data['winner__username']
            # Create a User instance with the id and username
            winner = User(id=winner_id, username=winner_username)
            winners.append(winner)
        logger.debug(f"Winners: {[winner.username for winner in winners]}")

        # If only one winner remains, the tournament is completed
        if len(winners) == 1:
            tournament.status = 'completed'
            await database_sync_to_async(tournament.save)()
            logger.debug(f"Tournament {tournament.id} completed. Winner: {winners[0].username}")
            return

        # Create next round matchups
        next_round = current_round + 1
        logger.debug(f"Creating matches for round {next_round}")
        for i in range(0, len(winners), 2):
            player1 = winners[i]
            player2 = winners[i+1] if (i+1) < len(winners) else None
            if player1 and player2:
                # Fetch full user objects asynchronously
                player1_full = await database_sync_to_async(User.objects.get)(id=player1.id)
                player2_full = await database_sync_to_async(User.objects.get)(id=player2.id)
                await database_sync_to_async(TournamentMatch.objects.create)(
                    tournament=tournament,
                    player1=player1_full,
                    player2=player2_full,
                    status='pending',
                    round_number=next_round
                )
                logger.debug(f"Match created: {player1.username} vs {player2.username}")
            elif player1 and not player2:
                # Fetch full user object asynchronously
                player1_full = await database_sync_to_async(User.objects.get)(id=player1.id)
                # Handle bye: player1 automatically advances
                await database_sync_to_async(TournamentMatch.objects.create)(
                    tournament=tournament,
                    player1=player1_full,
                    player2=None,
                    winner=player1_full,
                    status='completed',
                    round_number=next_round
                )
                logger.debug(f"Player {player1.username} advances by bye")
        # Recursive call to handle immediate progression
        await self.progress_tournament(tournament)

    @database_sync_to_async
    def associate_party_with_match(self, party_id, match_id):
        try:
            match = TournamentMatch.objects.get(id=match_id)
            party = Party.objects.get(id=party_id)
            match.party = party
            match.save()
        except TournamentMatch.DoesNotExist:
            pass
        except Party.DoesNotExist:
            pass
