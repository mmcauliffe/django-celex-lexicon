
from .models import FreqDict,Word,Spelling,Transcription


def checkDict(freqDict):
    if FreqDict.objects.filter(Name=freqDict).exists():
        return True
    return False

def lookupFreq(word):
    qs = Spelling.objects.filter(Label=word).order_by('-Word__Frequency')
    total = 0.0
    for q in qs:
        total += q.Word.Frequency
    return total

#def lookupStress(word,freqDict):
#    qs = Spelling.objects.filter(Label=word).order_by('-Word__Frequency')
#    return [q.StressPattern for q in qs]

def lookupCat(word):
    qs = Spelling.objects.filter(Label=word).order_by('-Word__Frequency')
    if len(qs) == 0:
        return 'NA'
    cat = qs[0].Word.Category.Label
    if cat == 'ADV':
        cat = 'R'
    return cat.lower()


