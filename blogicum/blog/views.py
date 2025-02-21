from datetime import datetime

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

from .models import Post, Category, Comment
from .forms import (
    EditUserProfileForm, CreatePostForm, CommentForm, CustomUserCreationForm
)

User = get_user_model()

COUNT_OF_POSTS = 10


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        obj = self.get_object()
        url = reverse('blog:post_detail', kwargs={'post_id': obj.pk})
        return redirect(url)


class UserCreateView(CreateView):
    model = User
    form_class = CustomUserCreationForm
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
        if self.kwargs['username'] == self.request.user.username:
            qs = self.model.objects
        else:
            qs = base_request()
        qs = qs.filter(author__username=self.kwargs['username'])
        return qs.annotate(
            comment_count=Count('comments')).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return context


class UpdatePostView(OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = CreatePostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class CreatePostView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = CreatePostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={
                'username': self.request.user.username
            })

    def get_object(self, queryset=None):
        return self.request.user


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        self.post_instance = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_instance
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentUpdateView(OnlyAuthorMixin, UpdateView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    form_class = CommentForm

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentDeleteView(OnlyAuthorMixin, DeleteView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


def base_request():
    """Функция выполняющая базовый запрос."""
    return Post.objects.all().select_related(
        'category',
        'location',
        'author'
    ).filter(
        pub_date__lt=datetime.now(),
        is_published=True,
        category__is_published=True
    )


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'page_obj'
    paginate_by = COUNT_OF_POSTS
    queryset = base_request().annotate(
        comment_count=Count('comments')).order_by('-pub_date')


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
            queryset = self.get_queryset()
        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is not None:
            queryset = queryset.filter(pk=pk)
        obj = get_object_or_404(queryset, pk=pk)
        if obj.author == self.request.user:
            return obj
        else:
            qs = base_request()
            return get_object_or_404(qs, pk=pk)


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = COUNT_OF_POSTS

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        category_of_post = get_object_or_404(
            Category, slug=category_slug, is_published=True
        )
        return base_request().filter(
            category=category_of_post).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        category_of_post = get_object_or_404(
            Category, slug=category_slug, is_published=True
        )
        context['category'] = category_of_post
        return context
