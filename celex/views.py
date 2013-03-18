
import csv

from django.core.management import call_command
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.core.files import File

from .models import *
from .forms import *
from .helper import fetch_celex_resource
from .tasks import doReset,doStringSelect,doNGramAnalysis

#old
#call_command('reset','stimuli', interactive=False,verbosity=0)
#                txt = TextFile(Name='IPHOD',
#                               Description='Irvine Phonological Online Dictionary',
#                               Path=File(open(fetch_media_resource('Iphod/iphod.txt'))),
#                               FrequencyFormat='M')
#                txt.save()
#                iphod = open(txt.Path.path).read().splitlines()
#                head = iphod.pop(0)
#                wq = []
#                ulq = []
#                wordInd = Word.objects.order_by('-pk')[:5]
#                if len(wordInd) > 0:
#                    wordInd = wordInd[0].pk
#                else:
#                    wordInd = 0
#                for l in iphod:
#                    wordInd += 1
#                    line = l.split("\t")
#                    ortho = line[0]
#                    trans = line[1].split(".")
#                    stress = '['+''.join(re.findall(r'\d',line[2]))+']'
#                    freq = line[3]
#                    wq.append([txt.pk,ortho,stress,freq])
#                    for i in xrange(len(trans)):
#                        q = SegmentType.objects.get_or_create(File=txt,Label=trans[i])
#                        sType = q[0]
#                        if q[1]:
#                            sType.guessProperties()
#                        ulq.append([wordInd,sType.pk,i])
#                Word.objects.create_in_bulk(wq)
#                Underlying.objects.create_in_bulk(ulq)

@login_required
def index(request):
    return render(request,'celex/index.html',{})



@login_required
def reset(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            form = ResetForm(request.POST)
            if form.is_valid() and form.cleaned_data['reset']:
                doReset.delay()
                return redirect(index)
        form = ResetForm()
        return render(request,'celex/form.html',{'form':form})

@login_required
def string_selection(request):
    if request.method == 'POST':
        form = StringForm(request.POST)
        if form.is_valid():
            doStringSelect.delay(form.cleaned_data)
            return redirect(index)
    form = StringForm()
    return render(request,'celex/form.html',{'form':form})

@login_required
def analyze_ngrams(request):
    if request.method == 'POST':
        form = ResetForm(request.POST)
        if form.is_valid():
            doNGramAnalysis.delay()
            return redirect(index)
    form = ResetForm()
    return render(request,'celex/form.html',{'form':form})


#def getFreqBreaks(qs):
    #freqs = sorted(qs.values_list('Frequency',flat=True))
    #print freqs[:15]
    #upper = freqs[(len(freqs)+1)/2-1:]
    #thirdQuart = upper[(len(upper)+1)/2-1]
    #lower = freqs[:(len(freqs)+1)/2-1]
    #firstQuart = lower[(len(lower)+1)/2-1]
    #med = freqs[(len(freqs)+1)/2-1]
    #return firstQuart,med,thirdQuart


#@login_required
#def Kevin(request):
    #if request.user.is_superuser:
        #if request.method == 'POST':
            #form = ResetForm(request.POST)
            #if form.is_valid() and form.cleaned_data['reset']:
                #response = HttpResponse(mimetype='text/csv')
                #response['Content-Disposition'] = 'attachment; filename=cvcvrhyming.csv'
                #writer = csv.writer(response,delimiter="\t")
                #qs = Word.objects.filter(CVSkel__isnull = True)
                #if len(qs) > 0:
                    #for w in qs:
                        #w.CVSkel = w.getCVStruct()
                        #w.save()
                #qs = Word.objects.filter(Orthography__regex='^[a-z]').filter(CVSkel='CVCV')
                ##print qs
                #first,med,third = getFreqBreaks(qs)
                #writer.writerow(['Word','C','V','C','V','StressPattern','Freq','FreqBin'])
                #for w in qs:
                    #if w.Frequency <= first:
                        #Fbin = 1
                    #elif w.Frequency <= med:
                        #Fbin = 2
                    #elif w.Frequency <= third:
                        #Fbin = 3
                    #else:
                        #Fbin = 4
                    #writer.writerow([w.Orthography]+map(str,w.Transcription.all())+[w.StressPattern,w.Frequency,Fbin])
                #return response
            #else:
                #form = ResetForm()
                #render(request,'reset.html',{'form':form})
        #else:
            #form = ResetForm()
            #return render(request,'reset.html',{'form':form})
