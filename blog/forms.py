from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.apps import apps

ProfileModel = apps.get_model('users', 'Profile')
TwootModel = apps.get_model('blog', 'Twoot')
TicketModel = apps.get_model('blog', 'Ticket')
MessageModel = apps.get_model('blog', 'Message')
    
class DateInput(forms.DateInput):
    input_type = 'date'

class FollowForm(forms.Form):
    followbutton = forms.CharField()
    
class LikeForm(forms.Form):
    querypost = forms.CharField(required=False)
    relatedtwoot = forms.CharField()

class ReTwootForm(forms.Form):
    querypost = forms.CharField(required=False)
    relatedtwoot = forms.CharField()

class CreateTwootForm(forms.ModelForm):
    content = forms.CharField(max_length=10, required=False, widget=forms.TextInput(attrs={"placeholder":"WHAT'S POPPIN?!"}))
    image_content = forms.ImageField(required=False)
    last_url = forms.CharField(required=False)

    class Meta:
        model = TwootModel
        fields = ['content', 'image_content']

class CreateUserForm(UserCreationForm):
    email = forms.EmailField()
    display_name = forms.CharField(max_length=500)
    display_blurb = forms.CharField(max_length=10, required=False)
    location = forms.CharField(max_length=30, required=False)
    birth_date = forms.DateField(widget=DateInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'display_name', 'display_blurb', 'location', 'birth_date', 'password1', 'password2']


class EditUserForm(forms.ModelForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['email']

class EditProfileForm(forms.ModelForm):
    display_name = forms.CharField(max_length=500)
    display_blurb = forms.CharField(max_length=10, required=False)
    location = forms.CharField(max_length=30, required=False)
    birth_date = forms.DateField(widget=DateInput(format=('%Y-%m-%d'), attrs={'class':'searchbar-create-account searchbar', 'type':'date'}), required=False)
    picture = forms.ImageField()
    banner = forms.ImageField()

    class Meta:
        model = ProfileModel
        fields = ['display_name', 'display_blurb', 'location', 'birth_date', 'picture', 'banner']

class ContactAweInspiringModeratorForm(forms.ModelForm):
    email = forms.EmailField()
    content = forms.Textarea()

    class Meta:
        model = TicketModel
        fields = ['email', 'content']

class MessageForm(forms.ModelForm):
    content = forms.Textarea()

    class Meta:
        model = MessageModel
        fields = ['content']