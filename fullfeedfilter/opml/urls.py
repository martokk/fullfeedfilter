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
    path('', views.ManageOpmlView.as_view(), name='manage_opml'),

    path('import_opml_file/', views.handle_opml_file_import, name='handle_opml_file_import'),
    path('<username>/', views.download_opml, name='download_opml'),
    path('<username>/remote_rss/', views.download_opml_remote_rss, name='download_opml_remote_rss'),

]

