# game/forms.py

from django import forms
from .models import Party, Tournament

class CreatePartyForm(forms.ModelForm):
    class Meta:
        model = Party
        fields = ['num_players']
        labels = {
            'num_players': 'Number of players'
        }

class CreateTournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name']
        labels = {
            'name': 'Tournament Name'
        }