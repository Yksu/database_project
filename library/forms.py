from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *

from django.utils import timezone



class LoginForm(forms.Form):
    username = forms.CharField(label='User', max_length=100)
    password = forms.CharField(widget=forms.PasswordInput, max_length=100)


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        widgets = {
          'birthday': forms.DateInput(attrs={'type': 'date'}),
        }
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name',
                  'email', 'address', 'birthday']

class BuyBookForm(forms.Form):
    pass

class CreateBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['isbn', 'title', 'author_pseudonym', 'price', 'year_of_pub', 'image_url', 'category']

class RecommendBookForm(forms.Form):
    def __init__(self, *args, **kwargs):
        friends_choices = kwargs.pop('friends', None)
        super(RecommendBookForm, self).__init__(*args, **kwargs)
        self.fields['friend'] = forms.ChoiceField(
            required=True,
            label='Who do you want to recommend this book to?',
            choices = friends_choices,
        )

class WriteReviewForm(forms.Form):
    def __init__(self, *args, **kwargs):
        default_eval = kwargs.pop('default_eval', None)
        super(WriteReviewForm, self).__init__(*args, **kwargs)

        self.fields['evaluation'] = forms.ChoiceField(
            required=True,
            choices=[(i, i) for i in range(1, 6)],
            initial=default_eval,
        )
        self.fields['summary'] = forms.CharField(
            required=True,
            max_length=140,
            label='Summary or title for the review',
            help_text='Max. 140 characters',
        )
        self.fields['content'] = forms.CharField(
            required=True,
            max_length=5000,
            widget=forms.Textarea,
            help_text='Max. 5000 characters',
        )

class WriteCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
