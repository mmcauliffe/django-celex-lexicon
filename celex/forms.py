from django import forms

from .models import SyntacticCategory

class ResetForm(forms.Form):
    reset = forms.BooleanField(initial=True)

class StringForm(forms.Form):
    cvskel = forms.CharField(max_length=100,initial='CVC')
    #phone_length = forms.CharField(max_length=3)
    exclude_punctuation = forms.BooleanField(required=False,initial=True)
    exclude_titlecase = forms.BooleanField(required=False,initial=True)
    categories = forms.ModelMultipleChoiceField(queryset = SyntacticCategory.objects.all())
    return_orthography = forms.BooleanField(required=False,initial=True)
    return_transcription = forms.BooleanField(required=False,initial=True)

