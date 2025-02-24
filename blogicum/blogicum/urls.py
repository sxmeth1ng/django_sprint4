from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from blog.views import UserCreateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blog.urls')),
    path('pages/', include('pages.urls')),
    path('auth/registration/', UserCreateView.as_view(), name='registration'),
    path('auth/', include('django.contrib.auth.urls')),
]

handler404 = 'pages.views.error_404'
handler500 = 'pages.views.error_500'

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
