from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

def vulnerable_view(request):
    user_id = request.GET.get('user_id', '')
    query = f"SELECT * FROM auth_user WHERE id = {user_id};"

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

    if result:
        return HttpResponse(f"User: {result}")
    else:
        return HttpResponse("No user found.")

def script_view(request):
    comment = request.GET.get('comment', '')
    return render(request, 'security/script.html', {'comment': comment})

comment_list = []

def script_2_view(request):
    if request.method == "POST":
        content = request.POST.get('content')
        comment_list.append(content)
        return render(request, 'security/script_2.html', {'comments': comment_list})

    return render(request, 'security/script_2.html', {'comments': comment_list})

FAKE_PASSWORD_STORAGE = {
    'user1': 'bonjour'
}

@csrf_exempt
def csrf_view(request):
    username = 'user1'
    current_password = FAKE_PASSWORD_STORAGE.get(username)
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        FAKE_PASSWORD_STORAGE[username] = new_password
        return render(request, 'security/csrf_2.html', {'new_password': new_password})
    
    return render(request, 'security/csrf.html', {'current_password': current_password})