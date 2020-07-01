from django.urls import path, re_path
from . import views
from .views import (MainView, ProfileView, createaccount_view,
                   editprofile_view, ExploreView, FollowingView,
                   FollowerView, TwootDetailView, delete_post,
                   HelpView, MessagesView, MessageDetailView,
                   RepliesView, LikesView, CreateTwootView,
                   CreateCommentView, MainViewLatest, ExploreViewLatest, ExploreViewFancy)

urlpatterns = [
    path('', MainView.as_view(), name='main_view'),
    path('latest/', MainViewLatest.as_view(), name="main_view_latest"),
    path('explore/', ExploreView.as_view(), name='explore_view'),
    path('explore/latest/', ExploreViewLatest.as_view(), name='explore_view_latest'),
    path('explore/tags/', ExploreViewFancy.as_view(), name='explore_view_fancy'),
    path('profile/<username>/', ProfileView.as_view(), name='profile_view'),
    path('profile/<username>/replies/', RepliesView.as_view(), name='replies_view'),
    path('profile/<username>/likes/', LikesView.as_view(), name='likes_view'),
    path('createaccount/', createaccount_view, name='createaccount'),
    path('editprofile/', editprofile_view, name='editprofile'),
    path('following/<username>/', FollowingView.as_view(), name="follow_view"),
    path('followers/<username>/', FollowerView.as_view(), name="follower_view"),
    path('twoots/<int:pk>/', TwootDetailView.as_view(), name="twoot_detail_view"),
    path('delete/<int:pk>/', views.delete_post, name="deletepost"),
    path('help/', HelpView.as_view(), name="help_view"),
    path('messages/', MessagesView.as_view(), name="messages_view"),
    path('message/<int:pk>/', MessageDetailView.as_view(), name="message_detail_view"),
    path('twoot/', CreateTwootView.as_view(), name="create_twoot_view"),
    path('comment/<int:pk>/', CreateCommentView.as_view(), name="create_comment_view"),
]