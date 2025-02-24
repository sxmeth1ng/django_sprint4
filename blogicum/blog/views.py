from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (CreateView,
                                  ListView,
                                  UpdateView,
                                  DeleteView,
                                  DetailView)
from django.db.models import Count
from django.urls import reverse_lazy, reverse
from django.contrib.auth.forms import UserCreationForm

from .models import Post, Category, Comment
from .forms import (
    EditUserProfileForm, CreateUpdatePostForm, CommentForm
)

User = get_user_model()

COUNT_OF_POSTS = 10


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        obj = self.get_object()
        if self.raise_exception:
            raise PermissionDenied()
        else:
            url = reverse('blog:post_detail', kwargs={'post_id': obj.pk})
            return redirect(url)


class UserCreateView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('blog:index')


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = EditUserProfileForm
    template_name = 'blog/user.html'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={
                'username': self.get_object().username
            })

    def get_object(self, queryset=None):
        return self.request.user


class ProfileListView(ListView):
    model = Post
    paginate_by = COUNT_OF_POSTS
    template_name = 'blog/profile.html'

    def get_queryset(self):
        user = get_object_or_404(User, username=self.get_object())
        if self.request.user == user:
            qs = self.model.objects
        else:
            qs = base_request(False, True)
        qs = qs.filter(author__username=self.get_object())
        return qs.order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.get_object()
        )
        return context

    def get_object(self):
        return self.kwargs['username']


class UpdatePostView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = CreateUpdatePostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return self.object.get_absolute_url()


class CreatePostView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = CreateUpdatePostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostDeleteView(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    form_class = CommentForm

    def get_object(self):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if post:
            comment = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
            return comment

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentDeleteView(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )

    def get_object(self):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if post:
            comment = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
            return comment


def base_request(is_author=False, is_comment=False):
    """Функция выполняющая базовый запрос."""
    request = Post.objects.all().select_related(
        'category',
        'location',
        'author'
    )
    if not is_author:
        request = request.filter(
            pub_date__lt=datetime.now(),
            is_published=True,
            category__is_published=True
        )
    if is_comment:
        request = request.annotate(comment_count=Count('comments'))
    return request


class IndexView(ListView):
    template_name = 'blog/index.html'
    context_object_name = 'page_obj'
    paginate_by = COUNT_OF_POSTS
    queryset = base_request(False, True).order_by('-pub_date')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.filter(
            post__id=self.kwargs['post_id']).order_by('created_at')
        return context

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset().select_related(
                'category', 'location', 'author'
            )
        pk = self.kwargs.get(self.pk_url_kwarg)
        obj = get_object_or_404(queryset, pk=pk)
        if obj.author == self.request.user:
            return obj
        else:
            qs = base_request(is_comment=True)
            return get_object_or_404(qs, pk=pk)


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = COUNT_OF_POSTS

    def get_queryset(self):
        category_of_post = self.get_object()
        return base_request().filter(
            category=category_of_post).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_of_post = self.get_object()
        context['category'] = category_of_post
        return context

    def get_object(self):
        category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True
        )
        return category
