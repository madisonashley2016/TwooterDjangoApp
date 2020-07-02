import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from .models import Twoot, ReTwoot, Post, Ticket, Like, Group, GroupLink, Message, HashTag
from users.models import Profile, Follower, Person
from .helperfunctions import createReTwootAjax


class ButtonConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.group_name = "all"
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data_json = json.loads(text_data)
        message_type = data_json['type']
        user = self.scope['user']
        if message_type == 'like':
            like_id = int(data_json['like_id'])
            like_status = data_json['status']
            try:
                twoot = Twoot.objects.get(pk=like_id)
                try: #Have you already liked the post? Unlike it.
                    like = Like.objects.get(liker=user, twoot=twoot)
                    like.delete()
                except: #If not, then like it.
                    like = Like(liker=user, twoot=twoot)
                    like.save()
                    like.refresh_from_db()

                async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    {
                        'type' : 'like_button',
                        'like_id' : like_id,
                        'like_status' : like_status,
                        'user' : user.username
                    }
                )
            except:
                print("Consumer Like Exception!")

        if message_type == "create_twoot":
            twoot_html = data_json['twoot_html']
            twoot_html1 = data_json['twoot_html1']
            twoot_html2 = data_json['twoot_html2']
            followers = list(user.profile.getFollowers.values_list("username", flat=True))
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type' : 'create_twoot_button',
                    'twoot_html' : twoot_html,
                    'twoot_html1' : twoot_html1,
                    'twoot_html2' : twoot_html2,
                    'user' : user.username,
                    'followers' : followers,
                    'button_type' : 'create_twoot'
                }
            )
        if message_type == "create_comment":
            twoot_html = data_json['twoot_html']
            twoot_html1 = data_json['twoot_html1']
            twoot_html2 = data_json['twoot_html2']
            parent_pk = data_json['parent_pk']

            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type' : 'create_comment_button',
                    'twoot_html' : twoot_html,
                    'twoot_html1' : twoot_html1,
                    'twoot_html2' : twoot_html2,
                    'parent_pk' : parent_pk,
                    'user' : user.username,
                    'button_type' : 'create_comment'
                }
            )
        if message_type == "retwoot": #if retwoot button is clicked...
            rt_twoot_id = data_json['retwoot_twoot_id'] #Get the twoot in questions primary key. 
            status = data_json['status'] #Get whether the clicker has already retwooted this twoot or naw. 

            #people_who_have_retwooted_this_twoot = list(User.objects.filter(authee__twoots__pk=rt_twoot_id).values_list("username", flat=True))
            twoot = Twoot.objects.get(pk=rt_twoot_id)
            p = twoot.retwoot.all()
            people_who_have_retwooted_this_twoot = []
            people_who_have_liked_this_twoot = list(User.objects.filter(liked_posts__twoot=twoot).values_list("username", flat=True))
            for twoot in p:#Get everyone who has retwooted this twoot.
                people_who_have_retwooted_this_twoot.append(twoot.author.username)

            if status == "not_retwooted": #if you have not retwooted it yet, (first double check, for realness)
                try:
                    retwoot = ReTwoot.objects.get(author=user, twoots__pk=rt_twoot_id)
                except: #Create new retwoot. 
                    response = createReTwootAjax(self, rt_twoot_id, user)
                    followers = list(user.profile.getFollowers.values_list("username", flat=True)) #Get all of your followers
                    async_to_sync(self.channel_layer.group_send)(
                        self.group_name, #We gonna send the retwoot to you and all of ur followers. 
                        { #We want the status for you to change to retwooted on both the retwoot and the original post
                         #We want everyone who has already retwooted the twoot for it to show up as retwooted on the new retwoot. 
                            'type' : 'retwoot_button',
                            'twoot_html' : response["twoot_html"],
                            'twoot_html_trash' : response["twoot_html_trash"],
                            'twoot_html2' : response["twoot_html2"],
                            'twoot_html_retwoot' : response["twoot_html_retwoot"],
                            'twoot_html_retwoot_g' : response["twoot_html_retwoot_g"],
                            'twoot_html_like' : response["twoot_html_like"],
                            'twoot_html_like' : response["twoot_html_like_r"],
                            'twoot_html_last' : response["twoot_html_last"],
                            'twoot_id' : rt_twoot_id,
                            'followers' : followers,
                            'people_retwooted' : people_who_have_retwooted_this_twoot,
                            'people_liked' : people_who_have_liked_this_twoot,
                            'user' : user.username
                        }
                    )
            else: #If you have already retwooted this post, we try to delete the retwoot
                try: #We want the retwoot to disappear for you and everyone else, and we want the status to change to not retwooted just for you.
                    retwoot = ReTwoot.objects.get(author=user, twoots__pk=rt_twoot_id)
                    delete_id = retwoot.pk
                    retwoot.delete()
                    async_to_sync(self.channel_layer.group_send)(
                    self.group_name,
                    {
                        'type' : 'retwoot_delete',
                        'delete_id' : delete_id,
                        'twoot_id' : rt_twoot_id,
                        'user' : user.username
                    }
                )
                except:
                    print("Something strange is afoot when trying to delete a retwoot in consumer!")

    def retwoot_delete(self, event):
        delete_id = event['delete_id']
        twoot_id = event['twoot_id']
        username = event['user']
        if username == self.scope['user'].username: #If deleter, then change original post status to not retwooted and delete retwoot
            self.send(text_data=json.dumps ({
            'type' : 'retwoot_delete',
            'delete_id' : delete_id,
            'twoot_id' : twoot_id,
            'me' : True
            }))
        else:
            self.send(text_data=json.dumps ({ #If everyone else, just delete the retwoot.
            'type' : 'retwoot_delete',
            'delete_id' : delete_id,
            'twoot_id' : twoot_id,
            'me' : False
            }))

    def retwoot_button(self, event):
        twoot_html = event['twoot_html']
        twoot_html_trash = event['twoot_html_trash']
        twoot_html2 = event['twoot_html2']
        twoot_html_retwoot = event['twoot_html_retwoot']
        twoot_html_retwoot_g = event['twoot_html_retwoot_g']
        twoot_html_like = event['twoot_html_like']
        twoot_html_like_r = event['twoot_html_like_r']
        twoot_html_last = event['twoot_html_last']
        twoot_id = event['twoot_id']
        username = event['user']
        followers = event['followers']
        people_liked = event['people_liked']
        people_retwooted = event['people_retwooted']

        if username == self.scope['user'].username: #If sender then create new twoot, show retwooted for it, and for original psot
            twoot_html += twoot_html_trash #If sender, then include trash icon.
            twoot_html += twoot_html2
            twoot_html += twoot_html_retwoot_g #Green button
            if self.scope['user'].username in people_liked:
                twoot_html += twoot_html_like_r
            else:
                twoot_html += twoot_html_like
            twoot_html += twoot_html_last
            self.send(text_data=json.dumps ({
            'twoot_html' : twoot_html,
            'twoot_id' : twoot_id,
            'me' : True,
            'type' : 'retwoot'
            })) #If in ur followers, and also retwooted the post, show retwooted for the new post as well.
        elif self.scope['user'].username in followers and self.scope['user'].username in people_retwooted:
            twoot_html += twoot_html2
            twoot_html += twoot_html_retwoot_g #Green button
            if self.scope['user'].username in people_liked:
                twoot_html += twoot_html_like_r
            else:
                twoot_html += twoot_html_like
            twoot_html += twoot_html_last
            self.send(text_data=json.dumps ({
            'twoot_html' : twoot_html,
            'twoot_id' : twoot_id,
            'me' : False,
            'type' : 'retwoot'
            })) #IF just in ur followers, then just show the new retwoot.
        elif self.scope['user'].username in followers: #if channel is in my(senders) followers.
            twoot_html += twoot_html2
            twoot_html += twoot_html_retwoot #Grey button
            if self.scope['user'].username in people_liked:
                twoot_html += twoot_html_like_r
            else:
                twoot_html += twoot_html_like
            twoot_html += twoot_html_last
            self.send(text_data=json.dumps ({
            'twoot_html' : twoot_html,
            'twoot_id' : twoot_id,
            'me' : False,
            'type' : 'retwoot'
            }))
        else: #Everyone else can just see the original post increment up by one.
            self.send(text_data=json.dumps ({
            'twoot_id' : twoot_id,
            'me' : False,
            'type' : 'retwoot'
            }))


    def create_comment_button(self,event):
        twoot_html = event['twoot_html']
        twoot_html1 = event['twoot_html1']
        twoot_html2 = event['twoot_html2']
        parent_pk = event['parent_pk']
        username = event['user']
        
        if username == self.scope['user'].username:
            twoot_html += twoot_html1
            twoot_html += twoot_html2
            self.send(text_data=json.dumps ({
            'twoot_html' : twoot_html,
            'parent_pk' : parent_pk,
            'me' : True,
            'sender_username' : username,
            'type' : 'create_comment'
            }))
        else:
            twoot_html += twoot_html2
            self.send(text_data=json.dumps ({
            'twoot_html' : twoot_html,
            'parent_pk' : parent_pk,
            'me' : False,
            'sender_username' : username,
            'type' : 'create_comment'
        }))   

    def create_twoot_button(self,event):
        twoot_html = event['twoot_html']
        twoot_html1 = event['twoot_html1']
        twoot_html2 = event['twoot_html2']
        username = event['user']
        followers = event['followers']

        if username == self.scope['user'].username: #If channel is me(message sender)
            twoot_html += twoot_html1
            twoot_html += twoot_html2
            self.send(text_data=json.dumps ({
            'twoot_html' : twoot_html,
            'me' : True,
            'sender_username' : username,
            'type' : 'create_twoot'
            }))
        elif self.scope['user'].username in followers: #if channel is in my(senders) followers.
            twoot_html += twoot_html2
            self.send(text_data=json.dumps ({
            'twoot_html' : twoot_html,
            'me' : False,
            'sender_username' : username,
            'in_followers' : True,
            'type' : 'create_twoot'
            }))
        else: #Everyone else
            twoot_html += twoot_html2
            self.send(text_data=json.dumps ({
            'twoot_html' : twoot_html,
            'me' : False,
            'sender_username' : username,
            'in_followers' : False,
            'type' : 'create_twoot'
            }))

    def like_button(self, event):
        like_id = event['like_id']
        like_status = event['like_status']
        user = event['user']

        if like_status == "liked":
            like_status = "not_liked"
        elif like_status == "not_liked":
            like_status = "liked"
        
        i_am_liker = False
        if self.scope['user'].username == user:
            i_am_liker = True
        self.send(text_data=json.dumps ({
            'like_id': like_id,
            'status' : like_status,
            'i_am_liker': i_am_liker,
            'type' : 'like'
        }))
    
    def disconnect(self, close_node):
        #If person leaves, then it removes them from the group.
        async_to_sync(self.channel_layer.group_discard)( 
            self.group_name,
            self.channel_name
        )


class MessageConsumer(WebsocketConsumer):
    def connect(self):
        #First check if the user is logged in. If they are not, then close the channel.
        if self.scope['user'].is_anonymous:
            self.close()
        else:
            #When someone connects to the socket, add them to the group(Add their channel)(Group speicified in url)
            self.group_pk = self.scope['url_route']['kwargs']['pk'] #Get the group name from the url.
            async_to_sync(self.channel_layer.group_add)( #Add the channel to the group. Or create it you know.
                self.group_pk,
                self.channel_name
            )
            self.accept() #Accept the connection.

    

    def receive(self, text_data):
        text_data_json = json.loads(text_data) #Parses the JSON into a Python Dictionary.
        message = text_data_json['message'] #Just grabs the text, so its a string and not a dict.
       
        message_obj = self.save_message(message) #Save the message to the DB.
        message_time = message_obj.time.strftime("%b %d, %Y, %I:%M")
        am_or_pm = message_obj.time.strftime("%p")
        if am_or_pm == "PM":
            message_time += " p.m."
        else:
            message_time += " a.m."
        message_profile_picture = message_obj.sender.profile.picture.url
        async_to_sync(self.channel_layer.group_send)(
            self.group_pk,
            {
                'type' : 'chat_message',
                'message' : message,
                'username' : self.scope['user'].username,
                'time' : message_time,
                'picture_url' : message_profile_picture
            }
        )

    def chat_message(self, event): #i think here is where every channel gets its message that it received.
        message = event['message']
        username = event['username']
        time = event['time']
        picture_url = event['picture_url']

        self.send(text_data=json.dumps({ #json.dumps takes a python dict and turns it into json.
            'message' : message,
            'username' : username,
            'time' : time,
            'picture_url' : picture_url
        }))

    def disconnect(self, close_node):
        #If person leaves, then it removes them from the group.
        async_to_sync(self.channel_layer.group_discard)( 
            self.group_pk,
            self.channel_name
        )
        
    def save_message(self, message):
        new_message = Message() #Create message object, save to db.
        new_message.sender = self.scope['user']
        current_group = Group.objects.get(pk=self.group_pk)
        new_message.group = current_group
        new_message.content = message
        new_message.save()
        return new_message