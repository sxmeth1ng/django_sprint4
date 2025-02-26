from django import forms

from .models import User, Post, Comment


class EditUserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class CreateUpdatePostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = (
            'title',
            'text',
            'category',
            'location',
            'pub_date',
            'image'
        )
        wigdets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime_local'})
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'cols': '40', 'rows': '3'})
        }
