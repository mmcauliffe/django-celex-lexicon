import os

from django.conf import settings

def fetch_celex_resource(uri):
    path = os.path.join(settings.CELEX_ROOT,uri)
    return path

def fetch_media_resource(uri):
    path = os.path.join(settings.MEDIA_ROOT,uri)
    return path

def is_neighbour(transOne,transTwo):
    matches = 0
    for i in range(len(transOne)):
        if transOne[i] == transTwo[i]:
            matches += 1
    if matches == 2:
        return True
    return False

def get_phone_dist(transOne,transTwo):
    dist = 0
    for i in range(len(transOne)):
        if transOne[i] != transTwo[i]:
            dist += 1
    return dist


def fix_many_to_many():
    qs = WordForm.objects.all().prefetch_related('orthographies')
    l = lambda x: (x.orthography,x.word_form,x.frequency)
    for w in qs:
        dups = []
        ss = w.spelledas_set.all()
        for s in ss:
            if l(s) not in map(l,dups) and map(l,ss).count(l(s)) > 1:
                dups.append(s)
        for s in dups:
            s.delete()

def remove_nonoccurrences():
    Lemma.objects.filter(frequency=0.0).delete()
    WordForm.objects.filter(frequency=0.0).delete()
    SpelledAs.objects.filter(frequency=0.0).delete()
    bads = []
    for o in Orthography.objects.all():
        if o.get_frequency() == 0.0:
            bads.append(o)
    for t in Transcription.objects.all():
        if t.get_frequency == 0.0:
            bads.append(t)
    for i in bads:
        i.delete()
