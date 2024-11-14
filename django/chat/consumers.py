import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Room,Message,User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_slug']
        self.roomGroupName = 'chat_%s' % self.room_name
        
        await self.channel_layer.group_add(
            self.roomGroupName,
            self.channel_name
        )
        await self.accept()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.roomGroupName,
            self.channel_name
        )
        
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "chat_message")
        
        if message_type == "chat_message":
            # Existing message handling
            message = text_data_json["message"]
            username = text_data_json["username"]
            room_name = text_data_json["room_name"]

            await self.save_message(message, username, room_name)

            await self.channel_layer.group_send(
                self.roomGroupName, {
                    "type": "sendMessage",
                    "message": message,
                    "username": username,
                    "room_name": room_name,
                }
            )
        elif message_type == "game_invite":
            # Since we're handling invites via the view, you may not need to handle this here
            pass

    async def game_invite(self, event):
        sender = event['sender']
        recipient = event['recipient']
        party_id = event['party_id']

        # Send the game invitation to the client
        await self.send(text_data=json.dumps({
            'type': 'game_invite',
            'sender': sender,
            'recipient': recipient,
            'party_id': party_id
        }))

    async def sendMessage(self, event):
        message = event["message"]
        username = event["username"]
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message,
            "username": username
        }))
    
    @sync_to_async
    def save_message(self, message, username, room_name):
        print(username,room_name,"----------------------")
        user=User.objects.get(username=username)
        room=Room.objects.get(name=room_name)
        
        Message.objects.create(user=user,room=room,content=message)
