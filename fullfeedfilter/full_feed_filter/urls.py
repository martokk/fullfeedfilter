"""full_feed_filter URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from general import views
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.HomeView.as_view(), name='home'),
    path('join/', views.JoinView.as_view(), name='join'),
    path('help/', views.HelpView.as_view(), name='help'),
    path('pro/', views.ProView.as_view(), name='pro'),
    path('contact/', views.AboutView.as_view(), name='contact'),
    path('account/', views.ContactView.as_view(), name='account'),

    path('accounts/', include('allauth.urls')),
    path('feed/', include('feeds.urls'), name='feeds'),
    path('feeds/', include('feeds.urls'), name='feeds2'),
    path('opml/', include('opml.urls'), name='opml'),
    path('reports/', include('reports.urls'), name='reports'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns
