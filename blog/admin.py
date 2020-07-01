from django.contrib import admin
from .models import Twoot, ReTwoot, Post, Ticket, Message, Group, GroupLink
# Register your models here.
admin.site.register(Twoot)
admin.site.register(ReTwoot)
admin.site.register(Post)
admin.site.register(Ticket)
admin.site.register(Message)
admin.site.register(Group)
admin.site.register(GroupLink)