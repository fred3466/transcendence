from django.db import models
from django.contrib.auth.models import User
from enum import unique

class Room(models.Model):
    name = models.CharField(max_length=200)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_user1', default=1)
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_user2', default=2)
    slug = models.SlugField(max_length=200)

    def __str__(self):
        return self.name

class Message(models.Model):
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

