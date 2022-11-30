import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from full_feed_filter.settings import BASE_DIR
from .scripts.opml import ImportOpml, ExportOpml


class ManageOpmlView(TemplateView):
    template_name = 'opml/opml.html'


@login_required
def handle_opml_file_import(request: HttpRequest) -> HttpResponseRedirect:
    ImportOpml(file=request.FILES['file'], user=request.user)
    print("complete")
    return HttpResponseRedirect(reverse_lazy('feed_list'))


# DOWNLOAD OPML FILES
def download_opml(request: HttpRequest, username: str) -> HttpResponse:
    # Generate OPML File
    opml = ExportOpml(username=username, remote_rss_feeds=False)
    opml.write_opml_to_file()

    # Download OPML File
    opml_file = os.path.join(BASE_DIR, f"media/opml/{opml.opml_filename}")
    response = HttpResponse(open(opml_file, 'r').read(), content_type='text/xml')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(f"{opml.opml_filename}")
    return response


def download_opml_remote_rss(request: HttpRequest, username: str) -> HttpResponse:
    # Generate OPML File
    opml = ExportOpml(username=username, remote_rss_feeds=True)
    opml.write_opml_to_file()

    # Download OPML File
    opml_file = os.path.join(BASE_DIR, f"media/opml/{opml.opml_filename}")
    response = HttpResponse(open(opml_file, 'r').read(), content_type='text/xml')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(f"{opml.opml_filename}")
    return response
