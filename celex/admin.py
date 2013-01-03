
from django.contrib import admin

from .models import *
from .forms import *

#class SegmentTypeAdmin(admin.ModelAdmin):
#    model = SegmentType
#    list_display = ('Label','Syllabic','Obstruent','Nasal','Vowel')

#admin.site.register(SegmentType, SegmentTypeAdmin)

class WordAdmin(admin.ModelAdmin):
    model = Word
    list_display = ('Label','getSpellings')

admin.site.register(Word, WordAdmin)
