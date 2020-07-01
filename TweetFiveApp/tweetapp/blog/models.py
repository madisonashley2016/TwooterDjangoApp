from django.db import models
from django.contrib.auth.models import User
from model_utils.managers import InheritanceManager
#from time import time, ctime
import sys
import time
import datetime
from datetime import datetime, timezone, timedelta
from mptt.models import MPTTModel, TreeForeignKey

# Create your models here.

class Post(MPTTModel):
    time_posted = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, default=1, on_delete=models.CASCADE, related_name="authee")
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    weight = models.DecimalField(max_digits=19, decimal_places=10)
    objects = InheritanceManager()

    class MPTTMeta:
        order_insertion_by = ['time_posted']

    @property
    def time_posted_formatted(self):
        current_time = datetime.now(timezone.utc)
        time_elapsed = current_time - self.time_posted
        time_delta_day = timedelta(days=0, seconds=86400, microseconds=0);
        time_delta_hour = timedelta(days=0, seconds=3600, microseconds=0);
        time_delta_minute = timedelta(days=0, seconds=60, microseconds=0);
      
        seconds = time_elapsed.seconds
        hours = seconds // 3600
        seconds = seconds - (hours * 3600)
        minutes = seconds // 60
        seconds = seconds - (minutes * 60)

        if time_elapsed > time_delta_day:
            return f"{self.time_posted.strftime('%b %d')}"
        elif time_elapsed > time_delta_hour:
            return f"{hours}h"
        elif time_elapsed > time_delta_minute:
            return f"{minutes}m"
        else:
            return f"{seconds}s"
    
    @property
    def setWeight(self):
        self.weight = 99999999
        now = (datetime.now(timezone.utc)).timestamp()
        time_posted = self.time_posted.timestamp()
        difference = (now - time_posted) / 7200
        self.weight = (self.weight + self.total_likes) - difference
        self.save()
    
    def __str__(self):
        return str(self.author) + ":Post"

class Twoot(Post):
    content = models.CharField(max_length=500, blank=True, null=True)
    image_content = models.ImageField(upload_to="twoot_pics", blank=True, null=True)
    
    @property
    def total_likes(self):
        return self.likes.count()

    @property
    def total_retwoots(self):
        return self.retwoot.count()

    def __str__(self):
        return str(self.author) + ":" + str(self.content) + " Twoot"


class ReTwoot(Post):
    twoots = models.ForeignKey(Twoot, default=1, on_delete=models.CASCADE, related_name="retwoot")

    @property
    def total_likes(self):
        return self.twoots.likes.count()

    @property
    def total_retwoots(self):
        return self.twoots.retwoot.count()

    def __str__(self):
        return str(self.author.username) + " Retwoot"

class Like(models.Model):
    liker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="liked_posts")
    twoot = models.ForeignKey(Twoot, on_delete=models.CASCADE, related_name="likes")
    time = models.DateTimeField(auto_now_add=True)

class Ticket(models.Model):
    email = models.EmailField()
    content = models.TextField()
    status = models.BooleanField(default=True, null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)

    def string_status(self):
        if self.status == False:
            return "Closed"
        else:
            return "Open"

    def __str__(self):
        return self.string_status()


class Group(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="moderating", null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    @property
    def hasMessages(self):
        return True if self.my_messages.all().exists() else False
       
    @property
    def getMostRecentMessage(self):
        return self.my_messages.all().latest('time')
        
    def getMessages(self):
        return self.my_messages.all()
    
    @property
    def getMyUsers(self):
        users = User.objects.filter(my_groups__group__pk=self.pk)
        return users

    def __str__(self):
        return f'Group:{self.date_created}:{self.getMyUsers}'


class GroupLink(models.Model):
    user = models.ForeignKey(User, default=1, on_delete=models.CASCADE, related_name="my_groups")
    group = models.ForeignKey(Group, default=1, on_delete=models.CASCADE, related_name="my_users")
    def __str__(self):
        return f'GroupLink:{self.user.username} -> {self.group.name}'

class Message(models.Model):
    sender = models.ForeignKey(User, default=1, on_delete=models.CASCADE, related_name="sent_messages")
    group = models.ForeignKey(Group, default=1, on_delete=models.CASCADE, related_name="my_messages")
    content = models.TextField()
    image_content = models.ImageField(upload_to="message_pics", blank=True, null=True)
    time = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'Message:{self.sender}->Grp:{self.group.name} at {self.time}'

class HashTag(models.Model):
    mentions = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=19, decimal_places=10, default=0)
    name = models.CharField(max_length=500)
    initial_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} weight: {self.weight} mentions: {self.mentions}'

    @property
    def setWeight(self):
        self.weight = 99999999
        now = (datetime.now(timezone.utc)).timestamp()
        initial_time = self.initial_time.timestamp()
        difference = (now - initial_time) / 7200
        self.weight = (self.weight + self.mentions) - difference
        self.save()


