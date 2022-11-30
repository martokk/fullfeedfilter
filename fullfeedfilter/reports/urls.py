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
from . import views

urlpatterns = [

    # Feeds Views
    path('', views.ManageReportsView.as_view(), name='manage_reports'),

    path('hidden/', views.view_hidden_articles, name='view_hidden_articles'),
    path('hidden/feed/<feed_id>/', views.view_hidden_articles, name='view_hidden_articles_for_feed'),
    path('hidden/<int:timedelta_hours>/', views.view_hidden_articles, name='view_hidden_articles_timedelta_hours'),
    path('hidden/<username>/', views.view_hidden_articles, name='view_hidden_articles_username'),
    path('hidden/<username>/<int:date>/', views.view_hidden_articles, name='view_hidden_articles_date'),
    path('hidden/<username>/rss/', views.redirect_to_hidden_articles_rss, name='redirect_to_hidden_articles_rss'),

    path('invalid/', views.view_feed_validation_errors, name='view_feed_validation_errors'),
    path('invalid/ignore/<int:error_pk>', views.ignore_feed_validation_errors, name='ignore_feed_validation_errors'),
    path('invalid/rss/', views.redirect_to_feed_validation_errors_rss, name='redirect_to_feed_validation_errors_rss'),
]

