from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image, GifImagePlugin, ImageFile
from django.core.files.storage import default_storage as storage

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
    display_name = models.CharField(max_length=500)
    display_blurb = models.CharField(max_length=10, blank=True, null=True)
    location = models.CharField(max_length=30, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    date_joined = models.DateField(auto_now_add=True)
    #picture = models.ImageField(upload_to="profile_pics", default="profile_pics/roboraptor.jpg")
    picture = models.ImageField(upload_to="profile_pics", default="profile_pics/roboraptor.jpg")
    banner = models.ImageField(upload_to="banner_pics", default="facade.jpg")

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
        
    def save(self, *args, **kwargs):
        super(Profile, self).save(*args, **kwargs)
        #img = Image.open(self.picture.path)
        #fh = storage.open(self.picture.name, 'wb')
        fh = storage.open(self.picture.name, 'rb')
        img = Image.open(fh)
        fh.close()
        
        if img.height > img.width: #If image is not square. Then make it square.
            left = 0
            right = img.width
            top = (img.height - img.width) / 2
            bottom = (img.height + img.width) / 2
            img = img.crop((left, top, right, bottom))
        elif img.width > img.height:
            left = (img.width - img.height) / 2
            right = (img.width + img.height) / 2
            top = 0
            bottom = img.height
            img = img.crop((left, top, right, bottom))
        if img.height > 500 or img.width > 500: #If image is too big. Then make it smaller.
            output_size = (500,500)
            img.thumbnail(output_size)
        
        fh = storage.open(self.picture.name, 'wb')
        format = 'jpg'
        img.save(fh, format)
        fh.close()
        #img.save(self.picture.path)
        #img.save(self.picture.name)
    
        #banner_img = Image.open(self.banner.path)
        fh = storage.open(self.banner.name, 'rb')
        banner_img = Image.open(fh)
        fh.close()
        if banner_img.format != 'GIF':
            if banner_img.height > 600: #If too big
                output_size = (600, banner_img.width)
                banner_img.thumbnail(output_size)
            if banner_img.width > 1800: #If too big
                output_size = (banner_img.height, 1800)
                banner_img.thumbnail(output_size)

            fh = storage.open(self.banner.name, 'wb')
            format = 'jpg'
            banner_img.save(fh, format)
            fh.close()
            #banner_img.save(self.banner.path)
           # banner_img.save(self.banner.name)
 
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
