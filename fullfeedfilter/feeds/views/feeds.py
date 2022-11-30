import os
import sys

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import management
from django.forms import Form
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from feeds.models import Feeds, FeedValidation, Filters
from feeds.scripts.feed_validation import Feedparser
from full_feed_filter.settings import BASE_DIR, DOMAIN
from general.scripts import utils


class FeedListView(LoginRequiredMixin, ListView):
    model = Feeds
    template_name = "feeds/feed_list.html"

    def get_queryset(self) -> Feeds:
        return Feeds.objects.filter(user=self.request.user).order_by("name")

    def get_context_data(self, **kwargs) -> dict:
        # Call the base implementation first to get a context
        context = super(FeedListView, self).get_context_data(**kwargs)

        # Add extra context from another model
        feed_validation_errors = (
            FeedValidation.objects.filter(ignore=False).values_list("feed", flat=True).distinct()
        )
        context["feed_validation_errors_list"] = list(feed_validation_errors)
        return context


class FeedDetailView(LoginRequiredMixin, DetailView):
    template_name = "feeds/feed_view.html"
    model = Feeds
    fields = [
        "name",
        "url",
        "scraper",
        "folder",
        "remove_text",
        "stop_html",
        "report_hidden_articles",
    ]

    def get_context_data(self, **kwargs) -> dict:
        # Call the base implementation first to get a context
        context = super(FeedDetailView, self).get_context_data(**kwargs)

        # Add extra context from another model
        filters = Filters.objects.filter(feed=self.kwargs["pk"]).order_by("-action", "keyword")
        context["filters"] = filters

        rss_url = f"http://{DOMAIN}/feeds/{self.kwargs['pk']}/rss/"
        context["rss_url"] = rss_url

        # Feed Validation Errors
        feed_validation_errors = FeedValidation.objects.filter(feed=self.kwargs["pk"], ignore=False)
        errors_list = []

        for error in feed_validation_errors:

            # Split Error
            try:
                error_split = str(error.error).split("<", 1)
                for i, itm in enumerate(error_split):
                    error_split[i] = itm.replace("^", "").replace("\xa0", "").strip()
                    pass
                error_html = f"<li><small>{ error_split[0].strip() }:<br><small><i>{ '<' + error_split[1].strip() }</i></small></small></li>"
            except IndexError:
                error_html = f"<li><small>{ error.error }</small></li>"
            errors_list.append(error_html)
        context["feed_validation_errors"] = errors_list
        return context


class FeedCreateView(LoginRequiredMixin, CreateView):
    template_name = "feeds/feed_add.html"
    model = Feeds
    fields = ["url", "scraper", "folder", "remove_text", "stop_html", "report_hidden_articles"]

    def form_valid(self, form: Form) -> HttpResponse:
        form.instance.user = self.request.user

        # Validate RSS Feed
        try:
            feed = Feedparser(url=form.instance.url)
            form.instance.name = feed.title

            if not feed.is_valid:
                raise AttributeError()
        except AttributeError:
            form.add_error(
                "url", "Feedparser could not parse URL. Check if this is a valid RSS Feed."
            )
            return self.form_invalid(form)

        o = form.save()

        # Create filtered xml rss feed
        # output_file = os.path.join(BASE_DIR, f"temp.txt")
        management.call_command("build", feed_id=o.pk, verbose=False)

        return super().form_valid(form)

    def get_success_url(self) -> HttpResponse:
        message = f"RSS feed for '<b>{self.object.name}</b>' successfully added. "
        messages.add_message(self.request, messages.SUCCESS, message)
        return reverse("feed_view", args=(self.object.pk,))


class FeedUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "feeds/feed_edit.html"
    model = Feeds
    fields = [
        "name",
        "url",
        "scraper",
        "folder",
        "remove_text",
        "stop_html",
        "report_hidden_articles",
    ]

    def form_valid(self, form: Form) -> HttpResponse:
        try:
            feed = Feedparser(url=form.instance.url)
        except AttributeError:
            form.add_error(
                "url", "Feedparser could not parse URL. Check if this is a valid RSS Feed."
            )
            return self.form_invalid(form)

        if not feed.is_valid:
            form.handle_exception(
                "url", "Feedparser could not parse URL. Check if this is a valid RSS Feed."
            )
            return self.form_invalid(form)

        o = form.save()

        # Rebuild RSS Feed
        if "scraper" in form.changed_data:
            management.call_command(
                "build", feed_id=o.pk, verbose=False, rebuild_full_articles=True
            )
        else:
            management.call_command(
                "build", feed_id=o.pk, verbose=False, rebuild_full_articles=False
            )

        return super().form_valid(form)

    def get_success_url(self) -> HttpResponse:
        message = f"RSS feed for '<b>{self.object.name}</b>' successfully updated."
        messages.add_message(self.request, messages.SUCCESS, message)
        return reverse("feed_list", args=(), kwargs={})


class FeedDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "feeds/feed_delete.html"
    model = Feeds
    success_url = reverse_lazy("feed_list")

    def delete(self, request, *args, **kwargs) -> HttpResponse:
        rss_folder = os.path.join(BASE_DIR, f"rss/{kwargs['pk']}")
        utils.remove_folders(rss_folder)
        return super().delete(self, request, *args, **kwargs)

    def get_success_url(self) -> HttpResponse:
        message = f"RSS feed for '<b>{self.object.name}</b>' was successfully deleted."
        messages.add_message(self.request, messages.SUCCESS, message)
        return reverse("feed_list", args=(), kwargs={})


# HELPERS
@login_required
def handle_rebuild_feed(request: HttpRequest, feed_id: int) -> HttpResponse:
    management.call_command("build", feed_id=feed_id, verbose=True, rebuild_full_articles=False)

    feed = Feeds.objects.filter(id=feed_id).first()
    message = f"RSS feed for '<b>{feed.name}</b>' was successfully refreshed."
    messages.add_message(request, messages.SUCCESS, message)
    return HttpResponseRedirect(reverse_lazy("feed_list"))


@login_required
def handle_rebuild_full_articles(request: HttpRequest, feed_id: int) -> HttpResponse:
    management.call_command("build", feed_id=feed_id, verbose=True, rebuild_full_articles=True)

    feed = Feeds.objects.filter(id=feed_id).first()
    message = f"Full articles for '<b>{feed.name}</b>' was successfully rebuilt."
    messages.add_message(request, messages.SUCCESS, message)
    return HttpResponseRedirect(reverse_lazy("feed_list"))


# RSS REDIRECTS
def redirect_to_rss(request: HttpRequest, feed_pk: int) -> HttpResponse:
    feed = Feeds.objects.filter(pk=feed_pk).first()
    if feed is None:
        return HttpResponse("RSS FEED NOT FOUND")

    rss_xml_file = os.path.join(BASE_DIR, f"media/rss/{feed.id}/rss.xml")

    if not os.path.isfile(rss_xml_file):
        management.call_command("build", feed_id=feed_pk, verbose=False, no_threading=True)

    return HttpResponse(open(rss_xml_file, "r").read())
