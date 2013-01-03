from django.db import models
from .managers import BulkManager,chunks
import re

# Create your models here.
from .helper import fetch_celex_resource


class WordManager(BulkManager):
    tbl_name = 'celex_word'
    cols = ['FreqDict_id','Label','Category_id','Frequency']


class TranscriptionManager(BulkManager):
    tbl_name = 'celex_transcription'
    cols = ['Transcription','Word_id']

class SpellingManager(BulkManager):
    tbl_name = 'celex_spelling'
    cols = ['Label','Word_id']



class FreqDict(models.Model):
    Name = models.CharField(max_length=100)
    Description = models.CharField(max_length=250,blank=True,null=True)

    def __unicode__(self):
        return u'%s' % self.Name

    def getDir(self):
        return fetch_celex_resource('%s/' % self.Name)

    def loadInfo(self):
        Word.objects.filter(FreqDict=self).delete()
        #Dummy Segment loading
        #st = SegmentType.objects.get_or_create(Label="A")[0]
        #Category loading
        SyntacticCategory.objects.all().delete()
        self.loadCats()
        lemmas = self.loadLemmas()
        ss = []
        ts = []
        for key in lemmas:
            if int(lemmas[key]['CategoryNum']) > 12:
                continue
            cat = SyntacticCategory.objects.get(pk=int(lemmas[key]['CategoryNum']))
            w = Word.objects.create(pk=int(key),FreqDict=self,Label=lemmas[key]['Word'],Category=cat,Frequency=int(lemmas[key]['Freq']))
            for spell in lemmas[key]['Spellings']:
                ss.append(Spelling(Label=spell,Word=w))
            for trans in lemmas[key]['Transcriptions']:
                ts.append(Transcription(Transcription=trans,Word=w))
        Spelling.objects.bulk_create(ss)
        Transcription.objects.bulk_create(ts)


    def loadCats(self):
        f = open(fetch_celex_resource('Category/cats.txt')).read().splitlines()
        head = f.pop(0).split("\t")
        cats = []
        for line in f:
            l = line.split("\t")
            cats.append(SyntacticCategory(pk=int(l[0]),Label=l[1],Description=l[2],CategoryType=l[3]))
        SyntacticCategory.objects.bulk_create(cats)

    def loadLemmas(self):
        lemmas = self.loadOrthLemmas()
        lemmas = self.loadOrthWF(lemmas)
        lemmas = self.loadTranscriptions(lemmas)
        lemmas = self.addCategories(lemmas)
        return lemmas

    def loadOrthLemmas(self):
        f = open(fetch_celex_resource('Orthography/celex-orthography-lemmas.txt')).read().splitlines()
        out = {}
        head = f.pop(0).split("\\")
        for line in f:
            l = line.split("\\")
            spellings = [l[1]]
            nl = {'Word':l[1],'Freq':l[2]}
            if l[3] != '1':
                for i in range(8,len(l)):
                    if (i - 7) % 4 == 0:
                        spellings.append(re.sub(r'-(?!-)',r'',l[i]))
            nl['Spellings'] = set(spellings)
            out[l[0]] = nl
        return out

    def loadOrthWF(self,lemmas):
        f = open(fetch_celex_resource('Orthography/celex-orthography-wordforms.txt')).read().splitlines()
        head = f.pop(0).split("\\")
        for line in f:
            l = line.split("\\")
            spellings = [l[1]]
            if l[4] != '1':
                for i in range(9,len(l)):
                    if (i - 8) % 5 == 0:
                        spellings.append(re.sub(r'-(?!-)',r'',l[i]))
            lemmas[l[3]]['Spellings'].update(set(spellings))
        return lemmas

    def loadTranscriptions(self,lemmas):
        from .media.constants import CONVERSION
        f = open(fetch_celex_resource('Phonology/celex-phonology-lemmas.txt')).read().splitlines()
        head = f.pop(0).split("\\")
        for line in f:
            l = line.split("\\")
            main = l[:8]
            additional = l[8:]
            trans = [main[5]]
            if len(additional) != 0:
                additional = chunks(additional,4)
                trans.extend([x[1] for x in additional])
            lemmas[l[0]]['Transcriptions'] = set(trans)
        return lemmas


    def addCategories(self,lemmas):
        f = open(fetch_celex_resource('Category/celex-syntax-lemmas.txt')).read().splitlines()
        head = f.pop(0).split("\\")
        for line in f:
            l = line.split("\\")
            lemmas[l[0]]['CategoryNum'] = l[3]
        return lemmas



#class SegmentType(models.Model):
#    Label = models.CharField(max_length=10)
#    Syllabic = models.NullBooleanField()
#    Obstruent = models.NullBooleanField()
#    Nasal = models.NullBooleanField()
#    Vowel = models.NullBooleanField()
#
#    def guessProperties(self):
#        NasalInd = ['n','m']
#        VowelInd = set(['i','u','o','e','a'])
#        ApproxInd = ['r','l','y']
#        for s in self.Label.lower():
#            if s in VowelInd:
#                self.Vowel = True
#                break
#        else:
#            self.Vowel = False
#        self.save()
#
#    def isSyllabic(self):
#        return self.Syllabic
#
#    def isNasal(self):
#        return self.Nasal
#
#    def isObs(self):
#        return self.Obstruent
#
#    def isVowel(self):
#        return self.Vowel
#
#    def __unicode__(self):
#        return u'%s' % (self.Label,)
#
#
#class Underlying(models.Model):
#    Transcription = models.ForeignKey('Transcription')
#    SegmentType = models.ForeignKey(SegmentType)
#    Ordering = models.IntegerField()
#
#    objects = URManager()
#
#    class Meta:
#        ordering = ['Ordering']


class Transcription(models.Model):
    Transcription = models.CharField(max_length=250)
    StressPattern = models.CharField(max_length=100,blank=True,null=True)
    CVSkel = models.CharField(max_length=100,blank=True,null=True)
    Word = models.ForeignKey('Word')

    #def getCVStruct(self):
    #    if self.CVSkel is not None:
    #        return self.CVSkel
    #    cvstruct = ''
    #    for s in self.Transcription.all():
    #        if s.isVowel():
    #            cvstruct = cvstruct + 'V'
    #        else:
    #            cvstruct = cvstruct + 'C'
    #    self.CVSkel = cvstruct
    #    self.save()
    #    return cvstruct

class SyntacticCategory(models.Model):
    Label = models.CharField(max_length=50)
    Description = models.CharField(max_length=100,blank=True,null=True)
    CategoryType = models.CharField(max_length=100,blank=True,null=True)

#class CatRelationship(models.Model):
#    Word = models.ForeignKey('Word')
#    Category = models.ForeignKey(SyntacticCategory)
#    Count = models.BigIntegerField(blank=True,null=True)

#    class Meta:
#        ordering = ['-Count']

class Spelling(models.Model):
    Label = models.CharField(max_length=250)
    Word = models.ForeignKey('Word')

    def __unicode__(self):
        return u'%s' % self.Label

class Word(models.Model):
    FreqDict = models.ForeignKey(FreqDict)
    Label = models.CharField(max_length=250)
    Category = models.ForeignKey(SyntacticCategory)
    Frequency = models.FloatField(blank=True,null=True)
    ND = models.FloatField(blank=True,null=True)
    FWND = models.FloatField(blank=True,null=True)
    PhonoProb = models.FloatField(blank=True,null=True)

    #objects = WordManager()

    def getUR(self):
        return ".".join(str(s) for s in Transcription.objects.filter(Word=self))

    def getSpellings(self):
        return ", ".join(str(s) for s in Spelling.objects.filter(Word=self))

    #def getPrimaryCategory(self):
    #    if self.PrimaryCategory is not None:
    #        return self.PrimaryCategory
    #    self.PrimaryCategory = self.catrelationship_set.all()[0].Category.Label
    #    self.save()
    #    return self.PrimaryCategory
