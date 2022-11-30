from .models import Feeds, Filters
from django.forms import ModelForm


class FeedsForm(ModelForm):
    class Meta:
        model = Feeds
        exclude = ('user',)


class FiltersForm(ModelForm):
    class Meta:
        model = Filters
        fields = '__all__'
