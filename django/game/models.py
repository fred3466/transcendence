from django.db import models
from django.contrib.auth.models import User

class Party(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    num_players = models.IntegerField(choices=[(0, 'Play Local'), (1, 'Play with AI'), (2, '2 Players'), (3, '3 Players')], default=2)
    nbPlayer = models.IntegerField(default=0)  # Start with 1 since the creator joins immediately
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('in_progress', 'In Progress'), ('completed', 'Completed')],
        default='active'
    )
    participants = models.ManyToManyField(User, related_name='parties_joined', blank=True) 

    def __str__(self):
        return f"Party {self.id} by {self.creator.username}"

    class Meta:
        db_table = 'game_party'  # Custom table name

class LeaderboardEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opponent_entries', null=True, blank=True)
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    player_score = models.IntegerField()
    opponent_score = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        opponent_username = self.opponent.username if self.opponent else 'Unknown'
        return f"{self.user.username} vs {opponent_username} - {self.player_score} vs {self.opponent_score} at {self.timestamp}"

class Tournament(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    players = models.ManyToManyField(User, related_name='tournaments')
    status = models.CharField(
        max_length=20,
        choices=[('waiting', 'Waiting'), ('in_progress', 'In Progress'), ('completed', 'Completed')],
        default='waiting'
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True) 

    def __str__(self):
        return f"Tournament {self.name}"
    
class TournamentMatch(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    party = models.OneToOneField(Party, on_delete=models.SET_NULL, null=True, blank=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')],
        default='pending'
    )
    round_number = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True) 

    def __str__(self):
        return f"Match: {self.player1.username} vs {self.player2.username} ({self.tournament.name})"