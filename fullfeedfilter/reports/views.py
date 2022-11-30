import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.urls import reverse_lazy
from django.shortcuts import render
# noinspection PyProtectedMember,PyProtectedMember
from django.views.generic import TemplateView

from general.scripts import utils
from full_feed_filter.settings import BASE_DIR
from feeds.models import Feeds, FeedValidation

from reports.scripts.hidden_articles import HiddenArticleViewer


class ManageReportsView(TemplateView):
    template_name = 'reports/reports.html'


# HIDDEN ARTICLES
@login_required
def view_hidden_articles(request: HttpRequest, timedelta_hours=8, feed_id=None, *args, **kwargs) -> HttpResponse:
    _hidden_articles = HiddenArticleViewer(user=request.user,
                                           timedelta_hours=timedelta_hours,
                                           feed_id=feed_id)

    context = _hidden_articles.get_context()
    return render(request, template_name='reports/hidden_articles_view.html', context=context)


def redirect_to_hidden_articles_rss(request: HttpRequest, username: str) -> HttpResponse:
    rss_folder = os.path.join(BASE_DIR, f"media/hidden/{username}.xml")
    return HttpResponse(open(rss_folder, 'r').read())

# FEED VALIDATIONS
@login_required
def view_feed_validation_errors(request: HttpRequest) -> HttpResponse:
    invalid_feeds = FeedValidation.objects.values_list('feed', flat=True).distinct()

    feeds_errors = []
    for feed in invalid_feeds:
        feed = Feeds.objects.filter(pk=feed).first()
        feeds_errors.append({
            'feed': feed,
            'errors': FeedValidation.objects.filter(feed=feed),
        })

    context = {
        'feeds_errors': feeds_errors,
        # 'total_errors': total_errors,
        'build_date': utils.now_cst(),
    }

    return render(request, template_name='reports/validation_errors.html', context=context)


@login_required
def ignore_feed_validation_errors(request: HttpRequest, error_pk: int) -> HttpResponse:
    record = FeedValidation.objects.filter(id=error_pk).first()
    record.ignore = True
    record.save()
    return HttpResponseRedirect(reverse_lazy('view_feed_validation_errors'))


# noinspection PyUnusedLocal
def redirect_to_feed_validation_errors_rss(request: HttpRequest, date=None) -> HttpResponse:
    rss_folder = os.path.join(BASE_DIR, f"media/invalid/invalid_feeds.xml")
    return HttpResponse(open(rss_folder, 'r').read())
