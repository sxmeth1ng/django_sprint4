from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.shortcuts import redirect

from .models import Comment


class CommentMixin:
    model = Comment
    pk_url_kwarg = 'comment_id'

    def get_object(self):
        return get_object_or_404(
            self.model,
            pk=self.kwargs[self.pk_url_kwarg],
            post_id=self.kwargs['post_id']
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied()
        else:
            url = reverse(
                'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
            )
            return redirect(url)
