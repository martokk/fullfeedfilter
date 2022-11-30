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
from django.urls import path
from .views import feeds, filters

urlpatterns = [

    # Feeds Views
    path('', feeds.FeedListView.as_view(), name='feed_list'),
    path('list/', feeds.FeedListView.as_view(), name='feed_list'),
    path('add/', feeds.FeedCreateView.as_view(), name='feed_add'),
    path('<int:pk>', feeds.FeedDetailView.as_view(), name='feed_view'),
    path('<int:pk>/edit/', feeds.FeedUpdateView.as_view(), name='feed_edit'),
    path('<int:pk>/delete/', feeds.FeedDeleteView.as_view(), name='feed_delete'),

    # Feeds - Redirect to RSS
    path('<int:feed_pk>/rss/', feeds.redirect_to_rss, name='redirect_to_rss'),
    path('<int:feed_pk>/rss/hide/', feeds.redirect_to_rss, {'hide': True}, name='redirect_to_rss_hidden'),
    path('<int:feed_pk>/rss/<slug>/', feeds.redirect_to_rss, name='redirect_to_rss_with_slug'),

    # Feeds - Rebuild Feeds
    path('<int:feed_id>/rebuild/', feeds.handle_rebuild_feed, name='feed_rebuild'),
    path('<int:feed_id>/rebuild_full_articles/', feeds.handle_rebuild_full_articles, name='feed_rebuild_full_articles'),

    # Filters Views
    path('<int:pk>/filter/add/', filters.FilterCreateView.as_view(), name='filter_add'),
    path('<int:pk>/filter/add/domain/<domain>', filters.FilterCreateView.as_view(), name='filter_add_domain'),
    path('<int:pk>/filter/add/<keyword>', filters.FilterCreateView.as_view(), name='filter_add_keyword'),
    path('<int:feed_pk>/filter/<int:pk>', filters.FilterUpdateView.as_view(), name='filter_view'),
    path('<int:feed_pk>/filter/<int:pk>/edit/', filters.FilterUpdateView.as_view(), name='filter_edit'),
    path('<int:feed_pk>/filter/<int:pk>/delete/', filters.FilterDeleteView.as_view(), name='filter_delete'),
]

