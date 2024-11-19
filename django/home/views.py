from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import Score
from django.http import HttpResponse
from render_block import render_block_to_string

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
from django_htmx.http import HttpResponseClientRedirect
from django_htmx.http import push_url

# Typing pattern recommended by django-stubs:
# https://github.com/typeddjango/django-stubs#how-can-i-create-a-httprequest-thats-guaranteed-to-have-an-authenticated-user
class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails
    
import logging
# logger = logging.getLogger(__name__)
logger = logging.getLogger("home")
#fred

# @login_required(login_url='/users/login/?redirected=true')
# def welcome(request):
#     context = {
#         "show_alert": True,
#     }
#     if 'HTTP_HX_REQUEST' in request.META:
#         html = render_block_to_string('home/welcome.html', 'body', context)
#         return HttpResponse(html)
#     return render(request, 'home/welcome.html', context)


@login_required(login_url='/users/login/?redirected=true')
def welcome(request: HtmxHttpRequest):
    logger.debug("== welcome")
    context = {
        "show_alert": True,
    }
    template_name = "home/welcome.html"
    if request.htmx:
        template_name += "#my_htmx_content"
    if 'HTTP_HX_REQUEST' in request.META:
        html = render_block_to_string('home/welcome.html', 'body', context)
        return push_url(HttpResponse(html),'')
    return push_url(render(request, template_name, context),'')

def leaderboard(request: HtmxHttpRequest):
    logger.debug("== leaderboard")
    context = {
        'all_users': User.objects.all().order_by('-profile__wins'),
    }
    template_name = "home/leaderboard.html"
    if request.htmx:
        template_name += "#my_htmx_content"
    if 'HTTP_HX_REQUEST' in request.META:
        html = render_block_to_string('home/leaderboard.html', 'body', context)
        return push_url(HttpResponse(html),'')
    return push_url(render(request, template_name, context),'')
