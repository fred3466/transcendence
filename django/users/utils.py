from users.models import FriendRequest
import os
import requests

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = 'https://localhost/users/callback/'

def get_friend_request_or_false(sender, receiver):
    try:
        return FriendRequest.objects.get(sender=sender, receiver=receiver, is_active=True)
    except FriendRequest.DoesNotExist:
        return False

class Oauth42:
    def get_token(self, code):
        url = 'https://api.intra.42.fr/oauth/token'
        data = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"Token exchange failed: {response.status_code} - {response.text}")
            return None

    def get_user_data(self, access_token):
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://api.intra.42.fr/v2/me', headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to retrieve user data: {response.status_code} - {response.text}")
            return None