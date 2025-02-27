from datetime import datetime, timezone

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
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
from .mixins import OnlyAuthorMixin, CommentMixin

User = get_user_model()

COUNT_OF_POSTS = 10


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
        qs = get_filtered_qs(
            is_hidden=(self.request.user != self.get_object()),
            is_comment=True
        ).filter(author=self.get_object())
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_object()
        return context

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs['username'])


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


class CommentUpdateView(
    LoginRequiredMixin, OnlyAuthorMixin, CommentMixin, UpdateView
):
    template_name = 'blog/comment.html'
    form_class = CommentForm


class CommentDeleteView(
    LoginRequiredMixin, OnlyAuthorMixin, CommentMixin, DeleteView
):
    form_class = CommentForm
    template_name = 'blog/comment.html'


def get_filtered_qs(is_hidden=False, is_comment=False):
    """Функция выполняющая базовый запрос."""
    queryset = Post.objects.select_related(
        'category',
        'location',
        'author'
    )
    if is_comment:
        queryset = queryset.annotate(
            comment_count=Count('comments')).order_by('-pub_date')
    if is_hidden:
        queryset = queryset.filter(
            pub_date__lt=datetime.now(),
            is_published=True,
            category__is_published=True
        )
    return queryset


class IndexView(ListView):
    template_name = 'blog/index.html'
    context_object_name = 'page_obj'
    paginate_by = COUNT_OF_POSTS
    queryset = get_filtered_qs(is_hidden=True, is_comment=True)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.filter(
            post__id=self.kwargs['post_id']).order_by('created_at')
        return context

    def get_object(self):
        queryset = get_filtered_qs()
        obj = get_object_or_404(queryset, pk=self.kwargs['post_id'])
        if obj.author != self.request.user:
            if (not obj.is_published
                    or obj.pub_date > datetime.now(timezone.utc)
                    or not obj.category.is_published):
                raise Http404('Page not found')
        return obj


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = COUNT_OF_POSTS

    def get_queryset(self):
        category_of_post = self.get_object()
        return get_filtered_qs(is_hidden=True, is_comment=True).filter(
            category=category_of_post)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_of_post = self.get_object()
        context['category'] = category_of_post
        return context

    def get_object(self):
        return get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True
        )
