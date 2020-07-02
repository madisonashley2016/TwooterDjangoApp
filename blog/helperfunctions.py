from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Twoot, ReTwoot, Post, Ticket, Like, Group, GroupLink, Message, HashTag
from users.models import Profile, Follower, Person
from .forms import (CreateUserForm, EditProfileForm, EditUserForm, 
                    CreateTwootForm, FollowForm, LikeForm,
                    ReTwootForm, ContactAweInspiringModeratorForm, MessageForm)

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from datetime import datetime, timezone
from django.core import serializers
from django.db.models import Exists, OuterRef

def getLikesReTwoots(self, request, twoots): #Get all liked posts by current user. Tell if liked or not.
    for twoot in twoots:
        if isinstance(twoot, ReTwoot):
            twoot.twoots.is_liked = True if Like.objects.filter(liker=request.user, twoot=twoot.twoots).exists() else False
            twoot.twoots.is_retwooted = True if ReTwoot.objects.filter(author=request.user, twoots=twoot.twoots).exists() else False
        else:
            twoot.is_liked = True if Like.objects.filter(liker=request.user, twoot=twoot).exists() else False
            twoot.is_retwooted = True if ReTwoot.objects.filter(author=request.user, twoots=twoot).exists() else False

    return twoots

def trendingalg(twoots):
    for twoot in twoots:
        twoot.setWeight
    twoots.sort(key=lambda x: x.weight, reverse=True)
    return twoots

def post_retwootform(self, request, *args, **kwargs):
    if "retwootbutton" in request.POST:
        retwootform = ReTwootForm(request.POST)

        if retwootform.is_valid():
            user = request.user #Get current user.
            query = retwootform.cleaned_data['querypost']
            query = "?q=" + query
            pk = retwootform.cleaned_data['relatedtwoot']
            twoot = get_object_or_404(Twoot, pk=pk) #Get related Twoot.
            if twoot.retwoot.filter(author=user).exists(): #If you have retwooted, then delete the retwoot.
                retwootdelete = ReTwoot.objects.get(author=user, twoots=twoot)
                retwootdelete.delete()
            else: #Else create a new retwoot.
                retwoot = ReTwoot()
                retwoot.twoots = twoot
                retwoot.author = user
                retwoot.save()
    return query

def profileFollowButton(self, request, username):
    if request.method == "POST" and request.is_ajax():
        user = User.objects.get(username=username)
        try:
            follow = Follower.objects.get(follower=request.user, followed=user)
            follow.delete()
            return "unfollowed"
        except:
            follow = Follower()
            follow.follower = request.user
            follow.followed = user
            follow.save()
            return "followed"
    return "INCORRECT"

def createTwootAjax(self, request, response, *args, **kwargs):
    form = CreateTwootForm(request.POST, request.FILES)
    if form.is_valid():
        twoot = form.save(commit=False)

        content_split = twoot.content.split(" ") #Split the contents of the twoot up
        content_bk_together = ""
        for split in content_split: #Process contents, if ther is a hashtag, then turn into link
            if split.startswith("#"):
                split = split[1:]
                check_hashtags = HashTag.objects.filter(name=split)
                if(check_hashtags):
                    check_hashtags[0].mentions += 1
                    check_hashtags[0].save()
                else:
                    new_hashtag = HashTag(name=split, mentions=1)
                    new_hashtag.save()
                query = reverse('explore_view') + "?q=%23" + split
                split = '''<a href="{tag_url}">#{split}</a>'''.format(tag_url=query, split=split)
            content_bk_together += split + " " #Put htem all back togezzar
        twoot.content = content_bk_together #Save back into twoot quite good.
        user = request.user #Continue on with your day.
        twoot.author = user
        twoot.weight = 0
        twoot.save()
        response['twoot_html'] = '''<div data-url="{twoot_detail_view}" data-twoot-id="{pk}" class="twoot divgotourl"> 
                                        <div class="twoot-content-wrapper content">
                                            <div class="twoot-list-icon-div">
                                                <img class="icon" src="{twoot_icon_src}"/>
                                            </div>
                                        <div class="twoot-content-inner">
                                            <a class="content-author" href="{profile_view}">
                                            {display_name}</a>

                                            @{username}
                                            &#183; {time}'''.format(twoot_detail_view=reverse('twoot_detail_view', kwargs={'pk':twoot.pk}),
                                                                twoot_icon_src=twoot.author.profile.picture.url,
                                                                profile_view=reverse('profile_view', kwargs={'username':twoot.author.username}),
                                                                display_name=twoot.author.profile.display_name,
                                                                username=twoot.author.username,
                                                                time=twoot.time_posted_formatted, pk=twoot.pk)
        if twoot.is_child_node():
            response['twoot_html'] += '''Replying to <a href="{child_profile_view}">@{twoot_parent}</a>
            '''.format(child_profile_view=reverse('profile_view', kwargs={'username':twoot.parent.author.username}), twoot_parent=twoot.parent.author.username)                                                                                              
        response['twoot_html'] += '''<div class="twoot-content-true content-white">{content}</div>
        '''.format(content=twoot.content)

        if twoot.image_content:
            response['twoot_html'] += '''<span style="display: inline-block;"><img class="twoot-content-img" src="{content_image}"></span>
            '''.format(content_image=twoot.image_content.url)
        response['twoot_html'] +=  '''<div class="twoot-button-div">'''

        response['twoot_html1'] = '''<div class="twoot-button-inner-div">
                                        <a class="red twoot-button" href="{delete_url}"><i class='bx bx-trash' ></i></a>
                                        </div>'''.format(delete_url=reverse('deletepost', kwargs={'pk':twoot.pk}))
        response['twoot_html2'] =  '''<div class="twoot-button-inner-div">
                                        <a href="{create_comment_url}" class="twoot-button"><i class='bx bx-conversation'></i></a>
                                        </div>
                                        <div class="twoot-button-inner-div">
                                        <button class="retwoot-button green-unclicked twoot-button" type="submit" data-id="{pk}" data-status="not_retwooted" name="retwootbutton"><i class='jam jam-refresh-reverse'></i></button>
                                        <span class="total-retwoots">{retwoots}</span>
                                        </div>
                                        <div class="twoot-button-inner-div">
                                        <button class="like-button red-unclicked twoot-button" type="submit" data-status="not_liked" data-id="{pk}" name="likebutton"><i class='bx bx-heart'></i></button>
                                        <span class="total-retwoots">{likes}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>'''.format(pk=twoot.pk, retwoots=twoot.total_retwoots,
                                likes=twoot.total_likes, create_comment_url=reverse('create_comment_view', kwargs={'pk':twoot.pk}))

def createCommentAjax(self, request, response, pk, *args, **kwargs):
    form = CreateTwootForm(request.POST, request.FILES)
    if form.is_valid():
        parent_twoot = Twoot.objects.get(pk=pk) #Get twoot you are replying to.
        user = request.user #Get yourself.
        twoot = form.save(commit=False)

        content_split = twoot.content.split(" ") #Split the contents of the twoot up
        content_bk_together = ""
        for split in content_split: #Process contents, if ther is a hashtag, then turn into link
            if split.startswith("#"):
                split = split[1:]
                check_hashtags = HashTag.objects.filter(name=split)
                if(check_hashtags):
                    check_hashtags[0].mentions += 1
                    check_hashtags[0].save()
                else:
                    new_hashtag = HashTag(name=split, mentions=1)
                    new_hashtag.save()
                query = reverse('explore_view') + "?q=%23" + split
                split = '''<a href="{tag_url}">#{split}</a>'''.format(tag_url=query, split=split)
            content_bk_together += split + " " #Put htem all back togezzar
        twoot.content = content_bk_together #Save back into twoot quite good.
        twoot.author = user
        twoot.parent = parent_twoot #He becomes your motha and fatha.
        twoot.weight = 0
        twoot.save()#Save your new comment :D
        response['twoot_html'] = '''<div data-url="{twoot_detail_view}" data-twoot-id="{pk}" class="twoot divgotourl"> 
                                        <div class="twoot-content-wrapper content">
                                            <div class="twoot-list-icon-div">
                                                <img class="icon" src="{twoot_icon_src}"/>
                                            </div>
                                        <div class="twoot-content-inner">
                                            <a class="content-author" href="{profile_view}">
                                            {display_name}</a>

                                            @{username}
                                            &#183; {time}'''.format(twoot_detail_view=reverse('twoot_detail_view', kwargs={'pk':twoot.pk}),
                                                                twoot_icon_src=twoot.author.profile.picture.url,
                                                                profile_view=reverse('profile_view', kwargs={'username':twoot.author.username}),
                                                                display_name=twoot.author.profile.display_name,
                                                                username=twoot.author.username,
                                                                time=twoot.time_posted_formatted, pk=twoot.pk)
        if twoot.is_child_node():
            response['twoot_html'] += '''Replying to <a href="{child_profile_view}">@{twoot_parent}</a>
            '''.format(child_profile_view=reverse('profile_view', kwargs={'username':twoot.parent.author.username}), twoot_parent=twoot.parent.author.username)                                                                                              
        response['twoot_html'] += '''<div class="twoot-content-true content-white">{content}</div>
        '''.format(content=twoot.content)

        if twoot.image_content:
            response['twoot_html'] += '''<span style="display: inline-block;"><img class="twoot-content-img" src="{content_image}"></span>
            '''.format(content_image=twoot.image_content.url)
        response['twoot_html'] +=  '''<div class="twoot-button-div">'''

        response['twoot_html1'] = '''<div class="twoot-button-inner-div">
                                        <a class="red twoot-button" href="{delete_url}"><i class='bx bx-trash' ></i></a>
                                        </div>'''.format(delete_url=reverse('deletepost', kwargs={'pk':twoot.pk}))
        response['twoot_html2'] =  '''<div class="twoot-button-inner-div">
                                        <a href="{create_comment_url}" class="twoot-button"><i class='bx bx-conversation'></i></a>
                                        </div>
                                        <div class="twoot-button-inner-div">
                                        <button class="retwoot-button green-unclicked twoot-button" type="submit" data-id="{pk}" data-status="not_retwooted" name="retwootbutton"><i class='jam jam-refresh-reverse'></i></button>
                                        <span class="total-retwoots">{retwoots}</span>
                                        </div>
                                        <div class="twoot-button-inner-div">
                                        <button class="like-button red-unclicked twoot-button" type="submit" data-status="not_liked" data-id="{pk}" name="likebutton"><i class='bx bx-heart'></i></button>
                                        <span class="total-retwoots">{likes}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>'''.format(pk=twoot.pk, retwoots=twoot.total_retwoots,
                                    likes=twoot.total_likes, create_comment_url=reverse('create_comment_view', kwargs={'pk':twoot.pk}))
        response['parent_pk'] = pk

def createReTwootAjax(self, pk, user):
    response = {}
    twoot = Twoot.objects.get(pk=pk)
    retwoot = ReTwoot(twoots=twoot, author=user, weight=0)
    retwoot.save()

    response["twoot_html"] = '''
    <div data-url="{twoot_detail_view}" data-twoot-id="retwoot_{retwoot_pk}" class="twoot divgotourl"> 
        <div class="retwoot-twoot-text-div">
            <a class="content" href="{retwoot_profile_view}"> 
            <i class='jam jam-refresh-reverse'></i> {retwoot_display_name} Retwooted</a>
        </div> 
            <div class="twoot-content-wrapper content">
                <div class="twoot-list-icon-div">
                    <img class="icon" src="{twoot_icon_src}"/>
                </div>
            <div class="twoot-content-inner">
                <a class="content-author" href="{profile_view}">
                {display_name}</a>

                @{username}
                &#183; {time}'''.format(twoot_detail_view=reverse('twoot_detail_view', kwargs={'pk':twoot.pk}),
                                    twoot_icon_src=twoot.author.profile.picture.url,
                                    profile_view=reverse('profile_view', kwargs={'username':twoot.author.username}),
                                    display_name=twoot.author.profile.display_name,
                                    username=twoot.author.username,
                                    time=twoot.time_posted_formatted,
                                    retwoot_profile_view=reverse('profile_view', kwargs={'username':retwoot.author.username}),
                                    retwoot_display_name=retwoot.author.profile.display_name, retwoot_pk=retwoot.pk)
    if twoot.is_child_node():
        response["twoot_html"] += '''Replying to <a href="{child_profile_view}">@{twoot_parent}</a>
        '''.format(child_profile_view=reverse('profile_view', kwargs={'username':twoot.parent.author.username}), twoot_parent=twoot.parent.author.username)                                                                                              
    
    response["twoot_html"] += '''<div class="twoot-content-true content-white">{content}</div>
    '''.format(content=twoot.content)

    if twoot.image_content:
        response["twoot_html"] += '''<span style="display: inline-block;"><img class="twoot-content-img" src="{content_image}"></span>
        '''.format(content_image=twoot.image_content.url)
    response["twoot_html"] += '''<div class="twoot-button-div">'''
    response["twoot_html_trash"] = '''<div class="twoot-button-inner-div">
                                    <a class="red twoot-button" href="{delete_url}"><i class='bx bx-trash' ></i></a>
                                </div>'''.format(delete_url=reverse('deletepost', kwargs={'pk':twoot.pk}))
    response["twoot_html2"] =  '''<div class="twoot-button-inner-div">
                                    <a href="{create_comment_url}" class="twoot-button"><i class='bx bx-conversation'></i></a>
                                    </div>'''.format(create_comment_url=reverse('create_comment_view', kwargs={'pk':twoot.pk}))

    response["twoot_html_retwoot"] = '''<div class="twoot-button-inner-div">
                                    <button class="retwoot-button green-unclicked twoot-button" type="submit" data-id="{pk}" data-status="not_retwooted" name="retwootbutton"><i class='jam jam-refresh-reverse'></i></button>
                                    <span class="total-retwoots">{retwoots}</span>
                                    </div>'''.format(pk=twoot.pk, retwoots=twoot.total_retwoots)

    response["twoot_html_retwoot_g"] = '''<div class="twoot-button-inner-div">
                                    <button class="retwoot-button green twoot-button" type="submit" data-id="{pk}" data-status="retwooted" name="retwootbutton"><i class='jam jam-refresh-reverse'></i></button>
                                    <span class="green-no-hover total-retwoots">{retwoots}</span>
                                    </div>'''.format(pk=twoot.pk, retwoots=twoot.total_retwoots)
#was html3
    response["twoot_html_like"] = '''<div class="twoot-button-inner-div">
                                    <button class="like-button red-unclicked twoot-button" type="submit" data-status="not_liked" data-id="{pk}" name="likebutton"><i class='bx bx-heart'></i></button>
                                    <span class="total-retwoots">{likes}</span>'''.format(pk=twoot.pk, likes=twoot.total_likes)
    response["twoot_html_like_r"] = '''<div class="twoot-button-inner-div">
                                    <button class="like-button red twoot-button" type="submit" data-status="liked" data-id="{pk}" name="likebutton"><i class='bx bxs-heart'></i></button>
                                    <span class="red-no-hover total-retwoots">{likes}</span>'''.format(pk=twoot.pk, likes=twoot.total_likes)
                  #was part of html3
    response["twoot_html_last"] = '''</div>
                            </div>
                        </div>
                    </div>'''
    return response