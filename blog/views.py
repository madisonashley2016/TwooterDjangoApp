from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView, View
from django.template.loader import render_to_string

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Twoot, ReTwoot, Post, Ticket, Like, Group, GroupLink, Message, HashTag
from users.models import Profile, Follower, Person
from .forms import (CreateUserForm, EditProfileForm, EditUserForm, 
                    CreateTwootForm, FollowForm, LikeForm,
                    ReTwootForm, ContactAweInspiringModeratorForm, MessageForm)

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count, F
from .helperfunctions import *

twoot_list_template = 'blog/twoot_list.html'

@login_required
def delete_post(request, pk=None):
    redirect_url = request.META.get('HTTP_REFERER', None) or '/'
    parsed_url = redirect_url.split('/')
    try:
        deleteboy = Twoot.objects.get(pk=pk)
        deleteboy.delete()
    except:
        print("Delete Post Exception.")
    if 'twoots' in parsed_url and int(parsed_url[4]) == pk: #If in detail view, need to go somewhere else after delete.
        return redirect('main_view')
    return redirect(redirect_url)

class MainView(LoginRequiredMixin, View):
    template_name = 'blog/main.html'
    def get(self, request, *args, **kwargs):
        context = {}
        twoots = list(Post.objects.select_subclasses().filter( #Get all posts 
                    Q(author__followers__follower=request.user) | #where I am following the author
                    Q(author=request.user) #or where I am the author
                    ).distinct())
        twoots = trendingalg(twoots) #Sort by trending
        getLikesReTwoots(self, request, twoots)
        #For pagination
        if request.is_ajax():
            self.template_name = twoot_list_template

        context["twoots"] = twoots
        return render(request, self.template_name, context)
    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            response = {}
            if request.is_ajax:
                createTwootAjax(self, request, response, *args, **kwargs)
                return JsonResponse(response)
        return redirect('main_view')
        
class MainViewLatest(LoginRequiredMixin, View):
    template_name = 'blog/main.html'
    def get(self, request, *args, **kwargs):
        context = {}
        twoots = Post.objects.select_subclasses().filter( #Get all posts 
                    Q(author__followers__follower=request.user) | #where I am following the author
                    Q(author=request.user) #or where I am the author
                    ).distinct().order_by("-time_posted") #Sort by time posted.
        getLikesReTwoots(self, request, twoots)
        #For pagination
        if request.is_ajax():
            self.template_name = twoot_list_template

        context["twoots"] = twoots
        return render(request, self.template_name, context)
    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            response = {}
            if request.is_ajax:
                createTwootAjax(self, request, response, *args, **kwargs)
                return JsonResponse(response)
        return redirect('main_view_latest')

class CreateTwootView(LoginRequiredMixin, View):
    template_name = 'blog/create_twoot.html'
    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, self.template_name, context)
    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            response = {}
            if request.is_ajax:
                createTwootAjax(self, request, response, *args, **kwargs)
                return JsonResponse(response)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))       

def get_blog_queryset(query=None):
    queryset = []
    queries = query.split(" ")
    for q in queries: #Filter based on what you inputted.
        posts = Twoot.objects.filter(
            Q(author__username__icontains=q) |
            Q(author__profile__display_name__icontains=q) |
            Q(content__icontains=q)
        ).exclude(parent__isnull=False).distinct() #Exclude if they have a parent. so if parent is not null.
        #Turn into proper queryset. 
        for post in posts:
            queryset.append(post)
    return list(set(queryset))

class ExploreView(LoginRequiredMixin, View):
    template_name = 'blog/explore.html'
    def get(self, request, *args, **kwargs):
        query = ""
        context = {}
        if request.GET: #There is only one get request on this page. The search bar.
            try:
                query = request.GET['q']
                context["query"] = str(query)
            except:
                pass
        twoots = get_blog_queryset(query) #Get the filtered results based on search bar.
        twoots = trendingalg(twoots)#Trending algorithm. Sort by popularity.
        getLikesReTwoots(self, request, twoots)
        #For pagination
        if request.is_ajax():
            self.template_name = twoot_list_template

        context["twoots"] = twoots
        return render(request, self.template_name, context)
    def post(self, request, *args, **kwargs):
        return redirect("explore_view")

class ExploreViewLatest(LoginRequiredMixin, View):
    template_name = 'blog/explore.html'
    def get(self, request, *args, **kwargs):
        query = ""
        context = {}
        if request.GET: #There is only one get request on this page. The search bar.
            try:
                query = request.GET['q']
                context["query"] = str(query)
            except:
                pass
        twoots = get_blog_queryset(query) #Get the filtered results based on search bar.
        twoots.sort(key=lambda x: x.time_posted, reverse=True) #Sort by Latest.

        getLikesReTwoots(self, request, twoots)
        #For pagination
        if request.is_ajax():
            self.template_name = twoot_list_template

        context["twoots"] = twoots
        return render(request, self.template_name, context)
    def post(self, request, *args, **kwargs):
        return redirect("explore_view")

class ExploreViewFancy(LoginRequiredMixin, View):
    template_name = 'blog/explore_tags.html'
    def get(self, request, *args, **kwargs):
        query = ""
        context = {}
        if request.GET: #There is only one get request on this page. The search bar.
            try:
                query = request.GET['q']
                context["query"] = str(query)
                return redirect(reverse("explore_view" + query))
            except:
                pass
        context["hashtags"] = trendingalg(list(HashTag.objects.all()))[:50]
        #For pagination
        if request.is_ajax():
            self.template_name = twoot_list_template
        return render(request, self.template_name, context)
    def post(self, request, *args, **kwargs):
        return redirect("explore_view")

class LikesView(LoginRequiredMixin, View):
    template_name = 'blog/profile.html'
    def get(self, request, username, *args, **kwargs):
        context = {}
        #This is to see if you are following the person or not.
        user = User.objects.get(username=username)
        user.is_followed = True if Follower.objects.filter(follower=request.user, followed=user).exists() else False
        context["user"] = user

        #Get all of the posts that they have liked.
        twoots = Twoot.objects.filter(likes__liker=user).order_by('-likes__time')
        getLikesReTwoots(self, request, twoots)
        context["twoots"] = twoots

        if request.is_ajax():
            self.template_name = twoot_list_template
        return render(request, self.template_name, context)
    def post(self, request, username, *args, **kwargs):
        return HttpResponse(profileFollowButton(self, request, username))

class RepliesView(LoginRequiredMixin, View):
    template_name = 'blog/profile.html'
    def get(self, request, username, *args, **kwargs):
        context = {}
        #This is to see if you are following the person or not.
        user = User.objects.get(username=username)
        user.is_followed = True if Follower.objects.filter(follower=request.user, followed=user).exists() else False
        context["user"] = user
        #Get all of profile users posts and comments.
        twoots = Post.objects.select_subclasses().filter(author=user).order_by("-time_posted")
        getLikesReTwoots(self, request, twoots)
        context["twoots"] = twoots

        if request.is_ajax():
            self.template_name = twoot_list_template
        return render(request, self.template_name, context)
    def post(self, request, username, *args, **kwargs):
        return HttpResponse(profileFollowButton(self, request, username))

class ProfileView(LoginRequiredMixin, View):
    template_name = 'blog/profile.html'
    def get(self, request, username, *args, **kwargs):
        context = {}
        #This is to see if you are following the person or not.
        user = User.objects.get(username=username)
        user.is_followed = True if Follower.objects.filter(follower=request.user, followed=user).exists() else False
        context["user"] = user
        #Get all of profile users posts such that they are not comments.
        twoots = Post.objects.select_subclasses().filter(Q(author=user) & Q(parent=None)).order_by("-time_posted")
        getLikesReTwoots(self, request, twoots)
        context["twoots"] = twoots

        if request.is_ajax():
            self.template_name = twoot_list_template
        return render(request, self.template_name, context)
    def post(self, request, username, *args, **kwargs):
        return HttpResponse(profileFollowButton(self, request, username))

class FollowingView(LoginRequiredMixin, View): #Get who I am following
    template_name = "blog/follower.html"
    def get(self, request, username, *args, **kwargs):
        user = User.objects.get(username=username)
        follow= user.profile.getFollowing
        return render(request, self.template_name, {"follow" : follow, "title":"Following"})
    def post(self, request, username, *args, **kwargs):
        if request.method == "POST":
            if request.is_ajax():
                data = request.POST.get('type', None)
                if data == "follow-button":
                    user_in_question = request.POST.get('user_in_question', None)
                    user_in_question = User.objects.get(username=user_in_question)
                    try:
                        follow = Follower.objects.get(follower=request.user, followed=user_in_question)
                        follow.delete()
                        return HttpResponse("unfollowed")
                    except:
                        follow = Follower(follower=request.user, followed=user_in_question)
                        follow.save()
                        return HttpResponse("followed")

class FollowerView(LoginRequiredMixin, View): #Get my followers.
    template_name = "blog/follower.html"
    def get(self, request, username, *args, **kwargs):
        user = User.objects.get(username=username)
        follow= user.profile.getFollowers
        return render(request, self.template_name, {"follow" : follow, "title":"Followers"})
    def post(self, request, username, *args, **kwargs):
        if request.method == "POST":
            if request.is_ajax():
                data = request.POST.get('type', None)
                if data == "follow-button":
                    user_in_question = request.POST.get('user_in_question', None)
                    user_in_question = User.objects.get(username=user_in_question)
                    try:
                        follow = Follower.objects.get(follower=request.user, followed=user_in_question)
                        follow.delete()
                        return HttpResponse("unfollowed")
                    except:
                        follow = Follower(follower=request.user, followed=user_in_question)
                        follow.save()
                        return HttpResponse("followed")

def createaccount_view(request):
    if request.method == "POST":
        form = CreateUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.profile.display_name = form.cleaned_data['display_name']
            user.profile.display_blurb = form.cleaned_data['display_blurb']
            user.profile.location = form.cleaned_data['location']
            user.profile.birth_date = form.cleaned_data['birth_date']
            user.save()
            return redirect("login")
    else:
        form = CreateUserForm()
    return render(request, "blog/createaccount.html", {'form' : form})
   
@login_required
def editprofile_view(request):
    if request.method == "POST":
        user_form = EditUserForm(request.POST, instance=request.user)
        profile_form = EditProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            custom = profile_form.save(False)
            custom.user = user
            custom.save()
            return redirect("profile_view", username=request.user.username)
    else:
        user_form = EditUserForm(instance=request.user)
        profile_form = EditProfileForm(instance=request.user.profile)
    return render(request, "blog/editprofile.html", {"user_form" : user_form, "profile_form" : profile_form})

class TwootDetailView(LoginRequiredMixin, View):
    template_name = "blog/twoot.html"
    def get(self, request, pk, *args, **kwargs):
        context = {}
        twoot = Twoot.objects.get(pk=pk) #Get the parent twoot.
        twoot.is_liked = True if Like.objects.filter(liker=request.user, twoot=twoot).exists() else False
        twoot.is_retwooted = True if ReTwoot.objects.filter(author=request.user, twoots=twoot).exists() else False
        twoots = Twoot.objects.filter(parent=twoot).order_by('-time_posted')
        getLikesReTwoots(self, request, twoots)

        context["twoot"] = twoot
        context["twoots"] = twoots
        context["is_detail_view"] = True

        if request.is_ajax():
            self.template_name = twoot_list_template
        return render(request, self.template_name, context)
    def post(self, request, pk, *args, **kwargs):
        return redirect("twoot_detail_view", pk=pk)
        
class CreateCommentView(LoginRequiredMixin, View):
    template_name = 'blog/create_comment.html'
    def get(self, request, pk, *args, **kwargs):
        context = {}
        return render(request, self.template_name, context)
    def post(self, request, pk, *args, **kwargs):
        if request.method == "POST":
            response = {}
            if request.is_ajax:
                createCommentAjax(self, request, response, pk, *args, **kwargs)
                return JsonResponse(response)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))              

class HelpView(View):
    template_name = "blog/help.html"

    def get(self, request, *args, **kwargs):
        context={}
        form = ContactAweInspiringModeratorForm()
        context["form"] = form
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            if "supreme-submit" in request.POST:
                form = ContactAweInspiringModeratorForm(request.POST)
                if form.is_valid():
                    ticket = form.save(commit=False)
                    ticket.email = form.cleaned_data['email']
                    ticket.content = form.cleaned_data['content']
                    ticket.status = True
                    ticket.save()
                    messages.success(request, "Message Sent!")
                    return redirect("help_view")
        return redirect("help_view")           

def get_user_queryset(query=None):
    queryset = {}
    count = 0
    queries = query.split(" ")
    for q in queries:
        users = User.objects.filter(
            Q(username__icontains=q) |
            Q(profile__display_name__icontains=q)
        ).values("username", "profile__display_name", "pk").distinct()
        for user in users:
            queryset[count] = user
            count += 1
    return queryset

class MessagesView(View):
    template_name = "blog/messages.html"
    def get(self, request, *args, **kwargs):
        context = {}
        query = ""
        #Get all of the groups i am associated with.
        inbox = Group.objects.filter(my_users__user=request.user)
        if request.method == "GET" and request.is_ajax(): #This is for the modal search bar. 
            query = request.GET['q']
            context["query"] = str(query)
            users = get_user_queryset(query)
            return JsonResponse(users, safe=False)
        
        users = request.user.profile.getFollowing
        context["users"] = users
        context["inbox"] = inbox
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            if "user-choice" in request.POST:
                choices = User.objects.filter(Q(pk__in=request.POST.getlist('choices')) | Q(pk=request.user.pk))
                group_final = []
                group = Group.objects.filter( #Get all groups where all of the users in choices are in them.
                    my_users__user__in=choices
                ).annotate(num=Count('my_users')).filter(num=choices.count())
                for g in group: #Get rid of any groups that have more than the choices in them.
                    if g.my_users.count() > choices.count():
                        pass
                    else:
                        group_final.append(g)
                if group_final: #If there is a group with all of the choices, just link to that one.
                    return redirect("message_detail_view", pk=group_final[0].pk)
                
                #else
                new_group = Group(admin=request.user)
                new_group.save()
                new_link = GroupLink(user=request.user, group=new_group)
                new_link.save()

                for user in choices:
                    if user != request.user:
                        new_link = GroupLink(user=user, group=new_group)
                        new_link.save()
                return redirect("message_detail_view", pk=new_group.pk)
        return redirect("messages_view")

class MessageDetailView(View):
    template_name = "blog/message.html"

    def get(self, request, pk, *args, **kwargs):
        #Get all messages from this group ever, with most recent at the bottom.
        context = {}
        group = Group.objects.get(pk=pk) #Gets the group
        messages = group.getMessages() #Gets all of the messages I should put a cap on this. With an option to access archived messages.
        context["group"] = group
        context["messages"] = messages
        return render(request, self.template_name, context)
    def post(self, request, pk, *args, **kwargs):
        if request.method == "POST" and request.is_ajax():
            data = request.POST.get('type', None)
            if data == "info-button":
                group = Group.objects.get(pk=pk) #Gets the group
                html = render_to_string('blog/message_info.html', {'group' : group, 'request' : request})
                return HttpResponse(html)
            elif data == "follow-button":
                user_in_question = request.POST.get('user_in_question', None)
                user_in_question = User.objects.get(username=user_in_question)
                try:
                    follow = Follower.objects.get(follower=request.user, followed=user_in_question)
                    follow.delete()
                    return HttpResponse("unfollowed")
                except:
                    follow = Follower(follower=request.user, followed=user_in_question)
                    follow.save()
                    return HttpResponse("followed")