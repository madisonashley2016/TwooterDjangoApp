from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image, ImageFile


class PersonManager(models.Manager):
    pass

class Person(User):
    objects = PersonManager()
    class Meta:
        proxy = True

class Follower(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")

    def __str__(self):
        return f"The Follower: {self.follower.username}-> The Followed: {self.followed.username}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=500, blank=True, null=True)
    display_blurb = models.CharField(max_length=10, blank=True, null=True)
    location = models.CharField(max_length=30, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    date_joined = models.DateField(auto_now_add=True)
    picture = models.ImageField(upload_to="media/profile_pics", default="media/profile_pics/default_user.png")
    banner = models.ImageField(upload_to="media/banner_pics", default="media/banner_pics/default_banner.jpg")

    def __str__(self):
        return self.user.username

    @property #Get who I am following
    def getFollowing(self):
        following = User.objects.filter(followers__follower=self.user)
        return following

    @property
    def getFollowers(self): #Get my followers
        followers = User.objects.filter(following__followed=self.user)
        return followers
 
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
