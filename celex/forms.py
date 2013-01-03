from django import forms

class ResetForm(forms.Form):
    reset = forms.BooleanField(initial=True)
