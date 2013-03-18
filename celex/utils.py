import os

from django.db.models import Sum

from .models import Lemma,WordForm,Orthography,Transcription



def lookupLemmaFreq(word):
    total_freq = sum([x.frequency for x in Lemma.objects.filter(wordform__orthographies__spelling = word).distinct()])
    return total_freq

def lookupWFFreq(word):
    total_freq = sum([x.frequency for x in WordForm.objects.filter(orthographies__spelling = word).distinct()])
    return total_freq

#def lookupStress(word,freqDict):
#    qs = Spelling.objects.filter(Label=word).order_by('-Word__Frequency')
#    return [q.StressPattern for q in qs]

def categorize_words(words):
    return [ '#'.join([x,lookupCat(x)]) for x in words]

def lookupCat(orth):
    word = lookupSpelling(orth)
    if word is None:
        return 'NA'
    cat = str(word.lemma.category)
    if cat == 'ADV':
        cat = 'R'
    return cat

def filterNGrams(ngram_path):
    qs = Orthography.objects.filter(word_form__frequency__gt=10)#.prefetch_related()
    #qs = qs.exclude(spelling__contains="'")
    #qs = qs.exclude(spelling__contains=".")
    #qs = qs.exclude(spelling__contains=",")
    #qs = qs.exclude(spelling__contains='"')
    spells = set([str(x) for x in qs])
    orig_path = os.path.join(ngram_path,'original')
    trim_path = os.path.join(ngram_path,'trimmed')
    files = os.listdir(orig_path)
    for f in files:
        with open(os.path.join(orig_path,f),'r') as infile:
            with open(os.path.join(trim_path,f),'w') as outfile:
                for line in infile:
                    l = line.strip().split("\t")
                    l[0] = l[0].split(" ")
                    bad_word_check = False
                    for i in l[0]:
                        if i not in spells:
                            bad_word_check = True
                            break
                    if bad_word_check:
                        continue
                    outfile.write('\t'.join([' '.join(l[0]),l[1]]))
                    outfile.write('\n')

def lookupSpelling(orth):
    try:
        o = Orthography.objects.filter(spelling = orth).prefetch_related('spelledas_set__word_form__lemma__category')[0]
    except IndexError:
        return None
    words = [x.word_form for x in o.spelledas_set.all()]
    if words == []:
        return None
    word = max(words,key=lambda x: (x.get_cond_prob_of_spelling(o)*x.get_probability())/o.get_probability())
    return word

# P(W|s) = P(s|W) * p(W)/P(s)

def get_lexical_info(orth):
    word = lookupSpelling(orth)
    if word is None:
        return {}
    nd,fwnd = word.get_neigh_density()
    sp,bp = word.get_phono_prob()
    output = {'Freq':word.get_norm_frequency(),
                'ND':nd,
                'FWND':fwnd,
                'SP':sp,
                'BP':bp,
                'Cat':str(word.lemma.category)}
    return output


