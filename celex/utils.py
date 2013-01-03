from django.conf import settings

from .models import *


def fetch_celex_resource(uri):
    path = os.path.join(settings.CELEX_ROOT,uri)
    return path

def loadCELEX():
    f = open(fetch_celex_resource("esl/esl.cd"),'r').read().splitlines()
    ns = {}
    for line in f:
        l = line.split("\\")
        ns[(l[1],l[3])] = int(l[2])
    return ns

def checkDict(freqDict):
    qs = TextFile.objects.filter(Name=freqDict).count()
    if qs != 0:
        return True
    return False

def lookupFreq(word,freqDict):
    qs = Word.objects.filter(TextFile__Name=freqDict).filter(Orthography=word)
    total = 0.0
    for q in qs:
        total += q.Frequency
    return total

def lookupStress(word,freqDict):
    qs = Word.objects.filter(TextFile__Name=freqDict).filter(Orthography=word)
    return [q.StressPattern for q in qs]

def lookupCat(word):
    qs = Spelling.objects.filter(Label=word).order_by('-Word__Frequency')
    if len(qs) == 0:
        return 'NA'
    cat = qs[0].Word.Category.Label
    if cat == 'ADV':
        cat = 'R'
    return cat.lower()



def getNouns():
    nouns = loadCELEX()
    ns = []
    for key in nouns:
        if key[1] != '1':
            continue
        ncount = nouns[key]
        ocount = 0
        for i in range(2,13):
            if (key[0],str(i)) in nouns:
                ocount += nouns[(key[0],str(i))]
        if ocount == 0:
            ns.append(key[0])
            continue
        if float(ncount)/ float(ocount) >= 0.5:
            ns.append(key[0])
    return ns
