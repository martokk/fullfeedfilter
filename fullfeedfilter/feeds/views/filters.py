from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.forms import Form
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from feeds.models import Feeds, Filters


class FilterCreateView(LoginRequiredMixin, CreateView):
    template_name = 'feeds/filter_add.html'
    model = Filters
    queryset = Filters.objects.all()
    fields = ['keyword', 'condition', 'source', 'action']

    def get_initial(self) -> dict:
        # Get the initial dictionary from the superclass method
        initial = super(FilterCreateView, self).get_initial()

        # Set Initial Values
        initial['condition'] = 'in'
        initial['source'] = 'feed'
        initial['action'] = 'hide'

        # Set Optional Keyword Value
        keyword = self.kwargs.get('keyword', None)
        domain = self.kwargs.get('domain', None)
        if keyword:
            initial['keyword'] = keyword
        if domain:
            initial['keyword'] = domain
            initial['source'] = 'link'

        return initial

    def form_valid(self, form: Form) -> HttpResponse:
        form.instance.user = self.request.user
        feed = Feeds.objects.get(id=self.kwargs.get('pk'))
        form.instance.feed = feed

        # Reject duplicate entries:
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error('keyword', f'Filter already exists (duplicate filters are not allowed).')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs) -> dict:
        context = super(FilterCreateView, self).get_context_data(**kwargs)

        feed = Feeds.objects.get(id=self.kwargs.get('pk'))
        context['feed'] = feed

        return context

    def get_success_url(self) -> HttpResponse:
        message = f"New filter was successfully created."
        messages.add_message(self.request, messages.SUCCESS, message)
        return super().get_success_url()


class FilterUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'feeds/filter_edit.html'
    model = Filters
    fields = ['keyword', 'condition', 'source', 'action']

    def form_valid(self, form: Form) -> HttpResponse:
        # Reject duplicate entries:
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error('keyword', f'Filter already exists (duplicate filters are not allowed).')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs) -> dict:
        context = super(FilterUpdateView, self).get_context_data(**kwargs)
        feed = Feeds.objects.get(id=self.kwargs.get('feed_pk'))
        context['feed'] = feed
        return context

    def get_success_url(self) -> HttpResponse:
        message = f"Filter was successfully updated."
        messages.add_message(self.request, messages.SUCCESS, message)
        return super().get_success_url()


class FilterDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'feeds/filter_delete.html'
    model = Filters
    success_url = reverse_lazy('feed_view')

    def delete(self, request: HttpResponse, *args, **kwargs) -> HttpResponse:
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super(FilterDeleteView, self).get_context_data(**kwargs)
        feed = Feeds.objects.get(id=self.kwargs.get('feed_pk'))
        context['feed'] = feed
        return context

    def get_success_url(self) -> HttpResponse:
        message = f"Filter was successfully deleted."
        messages.add_message(self.request, messages.SUCCESS, message)
        return reverse_lazy('feed_view',
                            kwargs={'pk': self.kwargs.get('feed_pk')})
