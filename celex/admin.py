
from django.contrib import admin

from .models import *
from .forms import *


class LemmaAdmin(admin.ModelAdmin):
    model = Lemma
    list_display = ('label','get_spellings')

admin.site.register(Lemma, LemmaAdmin)

class WordFormAdmin(admin.ModelAdmin):
    model = WordForm
    list_display = ('lemma','get_spellings','get_transcriptions')

admin.site.register(WordForm, WordFormAdmin)
