from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import Score
from django.http import HttpResponse
from render_block import render_block_to_string

@login_required(login_url='/users/login/?redirected=true')
def welcome(request):
	context = {
		"show_alert": True,
	}
	if 'HTTP_HX_REQUEST' in request.META:
		html = render_block_to_string('home/welcome.html', 'body', context)
		return HttpResponse(html)
	return render(request, 'home/welcome.html', context)

def leaderboard(request):
	context = {
		'all_users': User.objects.all().order_by('-profile__wins'),
	}
	if 'HTTP_HX_REQUEST' in request.META:
		html = render_block_to_string('home/leaderboard.html', 'body', context)
		return HttpResponse(html)
	return render(request, 'home/leaderboard.html', context)
