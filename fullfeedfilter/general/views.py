from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'general/home.html'


class JoinView(TemplateView):
    template_name = 'general/join.html'


class HelpView(TemplateView):
    template_name = 'general/help.html'


class AboutView(TemplateView):
    template_name = 'general/contact.html'


class ProView(TemplateView):
    template_name = 'general/pro.html'


class ContactView(TemplateView):
    template_name = 'general/account.html'
