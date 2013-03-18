import os
import re
import math

import cPickle as pickle

from celery import task,chord,group,chain
from celery.signals import task_success
from celery.utils.log import get_task_logger

from django.conf import settings

#from ngrams.utils import in_trigram_context_entropy

from .models import *
from .managers import BulkManager,chunks

from .helper import fetch_media_resource,get_phone_dist,is_neighbour

logger = get_task_logger(__name__)

def chunk_dict(d, n):
    allout = []
    temp = {}
    for k in d:
        if len(temp) == n:
            allout.append(temp)
            temp = {}
        temp[k] = d[k]
    allout.append(temp)
    return allout

@task()
def doReset():
    letters = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
    lemmas = loadLemmas()
    #lemma_job = group(addLemmas.si(x) for x in chunk_dict(lemmas,10000))
    wfs,spells,trans = loadWF()
    #wf_job = group(addWFS.si(x) for x in chunk_dict(wfs,10000))
    #spell_job = group(addSpells.si(x) for x in chunks(spells,10000))
    #trans_job = group(addTrans.si(x) for x in chunks(trans,10000))
    ajob = group([addLemmas.si(lemmas),addSpells.si(spells),addTrans.si(trans)])
    #reljob = group([addSpellRelationships.si(wfs),addTransRelationships.si(wfs)])
    spelljob = chord([collectSpellRelationships.si(wfs,l) for l in letters])(addSpellRelationships.s())
    transjob = chord([collectTransRelationships.si(wfs,l) for l in letters])(addTransRelationships.s())
    reljob = group([spelljob,transjob])
    c2 = (deleteall.si() | loadCats.si() | ajob | addWFS.si(wfs) | reljob)
    res = c2()
    res.get()


@task()
def loadCats():
    cats = []
    with open(fetch_celex_resource('Category/cats.txt'),'r') as f:
        head = None
        for line in f:
            l = line.strip().split("\t")
            if head is None:
                head = l
                continue
            cats.append(SyntacticCategory(pk=int(l[0]),label=l[1],description=l[2],categoryType=l[3]))
    SyntacticCategory.objects.bulk_create(cats)

@task()
def deleteall():
    WordForm.objects.all().delete()
    Transcription.objects.all().delete()
    Orthography.objects.all().delete()
    Lemma.objects.all().delete()
    SyntacticCategory.objects.all().delete()

@task()
def addLemmas(lemmas):
    ls = []
    for key in lemmas:
        if int(lemmas[key]['CategoryNum']) > 12:
            continue
        cat = SyntacticCategory.objects.get(pk=int(lemmas[key]['CategoryNum']))
        ls.append(Lemma(pk=int(key),label=lemmas[key]['Word'],category=cat,frequency=int(lemmas[key]['Freq'])))
    Lemma.objects.bulk_create(ls)

def loadLemmas():
    lemmas = loadOrthLemmas()
    #lemmas = loadTransLemmas(lemmas)
    lemmas = addCategories(lemmas)
    return lemmas

def loadWF():
    wfs,spells = loadOrthWF()
    wfs,trans = loadTransWF(wfs)
    spells = [(i+1,v) for i,v in enumerate(spells)]
    trans = [(i+1,v) for i,v in enumerate(trans)]
    return wfs,spells,trans

@task()
def collectSpellRelationships(wfs,l):
    wf = WordForm.objects.filter(lemma__label__istartswith=l)
    sas = []
    for w in wf:
        for s in wfs[str(w.pk)]['Spellings']:
            spell = Orthography.objects.get(spelling = s[0])
            sas.append(SpelledAs(word_form=w,orthography=spell,frequency=s[1]))
    SpelledAs.objects.bulk_create(sas)
    #return sas


@task()
def addSpellRelationships(out):
    pass
    #for l in out:
    #    SpelledAs.objects.bulk_create(l)

@task()
def collectTransRelationships(wfs,l):
    wf = WordForm.objects.filter(lemma__label__istartswith=l)
    pas = []
    for w in wf:
        for t in wfs[str(w.pk)]['Transcriptions']:
            pron = Transcription.objects.get(transcription = t)
            pas.append(PronouncedAs(word_form=w,transcription=pron))
    PronouncedAs.objects.bulk_create(pas)
    #return pas

@task()
def addTransRelationships(out):
    pass
    #for l in out:
    #    PronouncedAs.objects.bulk_create(l)

@task()
def addWFS(wfs):
    wfss = []
    for key in wfs:
        lem = Lemma.objects.filter(pk=int(wfs[key]['IdLemma']))
        if len(lem) != 1:
            continue
        wfss.append(WordForm(pk=int(key),lemma = lem[0],frequency = int(wfs[key]['Freq'])))
    WordForm.objects.bulk_create(wfss)

@task()
def addSpells(spells):
    ss = [Orthography(pk=s[0],spelling = s[1]) for s in spells]
    Orthography.objects.bulk_create(ss)

@task()
def addTrans(trans):
    ts = [Transcription(pk=t[0],transcription = t[1]) for t in trans]
    Transcription.objects.bulk_create(ts)


def loadOrthLemmas():
    lemmas = {}
    with open(fetch_celex_resource('Orthography/celex-orthography-lemmas.txt'),'r') as f:
        head = None
        for line in f:
            l = line.strip().split("\\")
            if head is None:
                head = l
                continue
            main = l[:8]
            additional = l[8:]
            #spellings = [l[1]]
            nl = {'Word':l[1],'Freq':l[2]}
            #if len(additional) != 0:
            #    additional = chunks(additional,4)
            #    spellings.extend([re.sub(r'-(?!-)',r'',x[3]) for x in additional])
            #nl['Spellings'] = set(spellings)
            lemmas[l[0]] = nl
    return lemmas


def addCategories(lemmas):
    with open(fetch_celex_resource('Category/celex-syntax-lemmas.txt'),'r') as f:
        head = None
        for line in f:
            l = line.strip().split("\\")
            if head is None:
                head = l
                continue
            lemmas[l[0]]['CategoryNum'] = l[3]
    return lemmas

def loadOrthWF():
    ss = set([])
    wfs = {}
    with open(fetch_celex_resource('Orthography/celex-orthography-wordforms.txt'),'r') as f:
        head = None
        for line in f:
            l = line.strip().split("\\")
            if head is None:
                head = l
                continue
            main = l[:9]
            additional = l[9:]
            spellings = [(main[1],main[6])]
            nl = {'IdLemma':l[3],'Freq':l[2]}
            if len(additional) != 0:
                additional = chunks(additional,5)
                spellings.extend([(x[0],x[2]) for x in additional])
            nl['Spellings'] = set(spellings)
            ss.update([x[0] for x in nl['Spellings']])
            wfs[main[0]] = nl
    return wfs,ss

def loadTransWF(wfs):
    ts = set([])
    with open(fetch_celex_resource('Phonology/celex-phonology-wordforms.txt'),'r') as f:
        head = None
        for line in f:
            l = line.strip().split("\\")
            if head is None:
                head = l
                continue
            main = l[:9]
            additional = l[9:]
            trans = [main[6]]
            if len(additional) != 0:
                additional = chunks(additional,4)
                trans.extend([x[1] for x in additional])
            wfs[main[0]]['Transcriptions'] = set(trans)
            ts.update(trans)
    return wfs,ts

#def loadTransLemmas(lemmas):
#    with open(fetch_celex_resource('Phonology/celex-phonology-lemmas.txt'),'r') as f:
#        head = None
#        for line in f:
#            l = line.strip().split("\\")
#            if head is None:
#                head = l
#                continue
#            main = l[:8]
#            additional = l[8:]
#            trans = [main[5]]
#            if len(additional) != 0:
#                additional = chunks(additional,4)
#                trans.extend([x[1] for x in additional])
#            lemmas[l[0]]['Transcriptions'] = set(trans)
#    return lemmas

@task()
def doStringSelect(form):
    qs = WordForm.objects.all()
    qs = qs.filter(lemma__category__in = form['categories']).select_related('lemma','lemma__category').prefetch_related('orthographies__word','transcriptions')
    if form['exclude_punctuation']:
        qs = qs.exclude(orthographies__spelling__contains="'")
        qs = qs.exclude(orthographies__spelling__contains=".")
        qs = qs.exclude(orthographies__spelling__contains=",")
        qs = qs.exclude(orthographies__spelling__contains='"')
    if form['exclude_titlecase']:
        qs = qs.exclude(orthographies__spelling__regex="^[A-Z]")
    qs = qs.filter(transcriptions__cvskel = form['cvskel'])
    qs = qs.filter(frequency__gt = 1500.0)
    comps = []
    print len(qs)
    for i in range(len(qs)):
        q = qs[i]
        if i % 500 == 0:
            print i
        if len(q.transcriptions.all()) != 1:
            continue
        for j in range(i+1,len(qs)):
            s = qs[j]
            if len(s.transcriptions.all()) != 1:
                continue
            comps.append((q,s))
    print(len(comps))
    count = 0
    for x in chunks(comps,100):
        count += 1
        with open(os.path.join(settings.TEMP_DIR,'celex-strings-%d.txt'%count),'w') as f:
            pickle.dump(x,f)

@task()
def doNGramAnalysis():
    files = sorted(filter(lambda x: x.startswith('celex-strings'),os.listdir(settings.TEMP_DIR)))
    c2 = chord(group([analyze_block.s(x) for x in chunks(files,115)]))(combine_results.s())
    c2.get()

@task()
def analyze_block(files):
    #output = []
    for f in files:
        with open(os.path.join(settings.TEMP_DIR,'output-'+f),'w') as file_handle:
            comp = pickle.load(open(os.path.join(settings.TEMP_DIR,f),'r'))
            for c in comp:
                q = c[0]
                s = c[1]
                t_one = str(q.transcriptions.all()[0])
                o_one = q.orthographies.all()
                t_two = str(s.transcriptions.all()[0])
                o_two = s.orthographies.all()
                phon_dist = str(get_phone_dist(re.sub('\'','',t_one),re.sub('\'','',t_two)))
                #if not is_neighbour(re.sub('\'','',t_one),re.sub('\'','',t_two)):
                #    if t_one != t_two:
                #        continue
                #    phon_dist = "homophone"
                #else:
                #    phon_dist = "neighbour"
                in_context_entropy = str(in_trigram_context_entropy(o_one,o_two))
                c_one = str(q.lemma.category.label)
                c_two = str(s.lemma.category.label)
                f_one = str(q.frequency)
                f_two = str(s.frequency)
                L_one = str(q.lemma.label)
                L_two = str(s.lemma.label)
                LFreq_one = str(q.lemma.frequency)
                LFreq_two = str(s.lemma.frequency)
                file_handle.write('\t'.join([':'.join(map(str,o_one)),':'.join(map(str,o_two)),t_one,t_two,
                                        c_one,c_two,f_one,f_two,L_one,L_two,
                                        LFreq_one,LFreq_two,phon_dist,in_context_entropy]))
                file_handle.write('\n')
            del comp

@task()
def combine_results(allout):
    with open(os.path.join(fetch_media_resource("Results"),"Celex","ConCon.txt"),'w') as f:
        f.write("\t".join(['orth_one','orth_two','trans_one','trans_two','cat_one',
                            'cat_two','freq_one','freq_two','lemma_one','lemma_two',
                            'lemma_freq_one','lemma_freq_two','phon_distance','in_context_entropy']))
        f.write("\n")
        for l in allout:
            for line in allout:
                f.write("\t".join(line))
                f.write("\n")

def in_trigram_context_entropy(wordOne,wordTwo):
    w_one = [x for y in wordOne for x in y.word.all()]
    w_two = [x for y in wordTwo for x in y.word.all()]
    w_one_contexts = {x.get_context(): x.count for x in w_one}
    w_two_contexts = {x.get_context(): x.count for x in w_two}
    w_one_contexts.update({x:0 for x in w_two_contexts if x not in w_one_contexts})
    w_two_contexts.update({x:0 for x in w_one_contexts if x not in w_two_contexts})
    #print(w_one_contexts)
    #print(w_two_contexts)
    #print w_one_contexts
    #print w_two_contexts
    c_w_one = sum([x.count for x in w_one])
    c_w_two = sum([x.count for x in w_two])
    #print(c_w_one)
    #print(c_w_two)
    context_ent = [entropy_calc(float(c_w_one),float(c_w_two),
                                float(w_one_contexts[x]),float(w_two_contexts[x])) for x in w_one_contexts]
    #print context_ent
    #print(context_ent)
    context_sum = sum(context_ent)
    #print(context_sum)
    return context_sum


def entropy_calc(cntOne,cntTwo,cntCOne,cntCTwo):
    #print cntOne
    #print cntTwo
    #print cntCOne
    #print cntCTwo
    pCGivenWords = (cntCOne + cntCTwo)/(cntOne + cntTwo)
    Entp = cntCOne / (cntCOne + cntCTwo)
    if Entp == 0.0:
        Entp = 0.0000001
    elif Entp == 1.0:
        Entp = 0.9999999
    HWordsGivenC = - (Entp * math.log(Entp)) - ((1-Entp) * math.log(1-Entp))
    return pCGivenWords * HWordsGivenC
