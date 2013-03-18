import math

from django.db import models
from django.db.models import Sum



# Create your models here.
from .managers import BulkManager,chunks
from .helper import fetch_celex_resource

UR_LOOKUP = """replace(
                    replace(
                        replace(
                        transcription,'-',''
                                ),'''',''
                            ),'"',''
                        )
                    ~ %s"""




class SyntacticCategory(models.Model):
    label = models.CharField(max_length=50)
    description = models.CharField(max_length=100,blank=True,null=True)
    category_type = models.CharField(max_length=100,blank=True,null=True)

    def __unicode__(self):
        return self.label




class Transcription(models.Model):
    transcription = models.CharField(max_length=250)
    stress_pattern = models.CharField(max_length=100,blank=True,null=True)
    cvskel = models.CharField(max_length=100,blank=True,null=True)
    log_frequency = models.FloatField(blank=True,null=True)
    neigh_den = models.IntegerField(blank=True,null=True)
    fwnd = models.FloatField(blank=True,null=True)
    sphone_prob = models.FloatField(blank=True,null=True)
    biphone_prob = models.FloatField(blank=True,null=True)

    def __unicode__(self):
        return self.transcription

    def strip_transcription(self):
        return self.transcription.replace('-','').replace("'",'').replace('"','')

    def get_frequency(self):
        if self.log_frequency is not None:
            return self.log_frequency
        count = self.pronouncedas_set.all().aggregate(count = Sum('word_form__frequency'))['count']
        if count is None:
            count = 0.0
        totCount = WordForm.objects.all().aggregate(totcount = Sum('frequency'))['totcount']
        normed_freq = (float(count))/float(totCount)
        log_freq = math.log((normed_freq * 1000000.0)+1.0,10)
        self.log_frequency = log_freq
        self.save()
        return log_freq

    def get_phono_prob(self):
        if self.sphone_prob is not None and self.biphone_prob is not None:
            return self.sphone_prob, self.biphone_prob
        any_segment = '.'
        patterns = []
        SPprob = 0.0
        BPprob = 0.0
        phones = self.strip_transcription()
        for i in range(len(phones)):
            patt = [any_segment] * i
            patt.append(phones[i])
            pattern = '^'+''.join(patt) +'.*$'
            totPattern = '^'+''.join([any_segment] * (i+1)) +'.*$'
            count = Transcription.objects.extra(
                    where = [UR_LOOKUP],
                    params = [pattern])
            totCount = Transcription.objects.extra(
                    where = [UR_LOOKUP],
                    params = [totPattern])
            SPprob += float(sum([x.get_frequency()
                                    for x in count])) / float(sum([x.get_frequency()
                                                                    for x in totCount]))
            if i != len(phones)-1:
                patt = [any_segment] * i
                patt.extend([phones[i],phones[i+1]])
                pattern = '^'+''.join(patt) +'.*$'
                totPattern = '^'+''.join([any_segment] * (i+2)) +'.*$'
                count = Transcription.objects.extra(
                    where = [UR_LOOKUP],
                    params = [pattern])
                totCount = Transcription.objects.extra(
                    where = [UR_LOOKUP],
                    params = [totPattern])
                BPprob += float(sum([x.get_frequency()
                                    for x in count])) / float(sum([x.get_frequency()
                                                                    for x in totCount]))
        SPprob = SPprob / float(len(phones))
        BPprob = BPprob / float(len(phones)-1)
        self.sphone_prob,self.biphone_prob = SPprob,BPprob
        self.save()
        return SPprob,BPprob


    def get_neigh_densities(self):
        if self.neigh_den is not None and self.fwnd is not None:
            return self.neigh_den,self.fwnd
        any_segment = '.'
        phones = self.strip_transcription()
        patterns = []
        for i in range(len(phones)):
            patt = phones[:i] #Substitutions
            patt += any_segment
            patt += phones[i+1:]
            patterns.append('^'+''.join(patt) +'$')
            patt = phones[:i] #Deletions
            patt += phones[i+1:]
            patterns.append('^'+''.join(patt) +'$')
            patt = phones[:i] #Insertions
            patt += any_segment
            patt += phones[i:]
            patterns.append('^'+''.join(patt) +'$')

        neighs = Transcription.objects.extra(
                    where = [UR_LOOKUP],
                    params = ['|'.join(patterns)])
        nd = len(neighs)
        fwnd = sum([ x.get_frequency() for x in neighs])
        self.neigh_den = nd
        self.fwnd = fwnd
        self.save()
        return self.neigh_den,self.fwnd

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

class Orthography(models.Model):
    spelling = models.CharField(max_length=250)

    def get_frequency(self):
        return self.spelledas_set.all().aggregate(count = Sum('frequency'))['count']

    def get_probability(self):
        return float(self.get_frequency())/float( SpelledAs.objects.all().aggregate(totcount = Sum('frequency'))['totcount'])

    def __unicode__(self):
        return self.spelling

class SpelledAs(models.Model):
    word_form = models.ForeignKey('WordForm')
    orthography = models.ForeignKey(Orthography)
    frequency = models.FloatField(blank=True,null=True)

class PronouncedAs(models.Model):
    word_form = models.ForeignKey('WordForm')
    transcription = models.ForeignKey(Transcription)

class WordForm(models.Model):
    lemma = models.ForeignKey('Lemma')
    orthographies = models.ManyToManyField(Orthography,through = 'SpelledAs')
    transcriptions = models.ManyToManyField(Transcription,through = 'PronouncedAs')
    frequency = models.FloatField(blank=True,null=True)

    def get_probability(self):
        return float(self.frequency)/float(
                WordForm.objects.all().aggregate(totcount =
                                            Sum('frequency'))['totcount'])

    def get_cond_prob_of_spelling(self,orth):
        count = self.spelledas_set.filter(orthography=orth)[0].frequency
        totcount = self.spelledas_set.all().aggregate(totcount = Sum('frequency'))['totcount']
        if totcount == 0:
            print self
            print [(x.orthography,x.frequency) for x in self.spelledas_set.all()]
        return float(count)/float(totcount)

    def get_norm_frequency(self):
        freq = math.log(
                    (float(self.frequency) * 1000000)/float(WordForm.objects.all().aggregate(totcount = Sum('frequency'))['totcount']),10)
        return freq

    def get_neigh_density(self):
        nd_sum = 0
        fwnd_sum = 0.0
        for t in self.transcriptions.all():
            nd,fwnd = t.get_neigh_densities()
            nd_sum += nd
            fwnd_sum += fwnd
        nd = float(nd_sum)/float(len(self.transcriptions.all()))
        fwnd = float(fwnd_sum)/float(len(self.transcriptions.all()))
        return nd,fwnd

    def get_phono_prob(self):
        sp_sum = 0
        bp_sum = 0.0
        for t in self.transcriptions.all():
            sp,bp = t.get_phono_prob()
            sp_sum += sp
            bp_sum += bp
        sp = float(sp_sum)/float(len(self.transcriptions.all()))
        bp = float(bp_sum)/float(len(self.transcriptions.all()))
        return sp,bp


    def get_transcriptions(self):
        return ".".join(str(t) for t in self.transcriptions.all())

    def get_spellings(self):
        return ", ".join(str(s) for s in self.orthographies.all())

    def __unicode__(self):
        return u'%s' % self.lemma.label

class Lemma(models.Model):
    label = models.CharField(max_length=250)
    category = models.ForeignKey(SyntacticCategory)
    frequency = models.FloatField(blank=True,null=True)

    #objects = WordManager()
    def __unicode__(self):
        return self.label

    def get_transcriptions(self):
        return ".".join(str(t) for wf in WordForm.objects.filter(lemma=self) for t in wf.transcriptions.all())

    def get_spelling_set(self):
        return {str(s) for wf in WordForm.objects.filter(lemma=self) for s in wf.orthographies.all()}

    def get_spellings(self):
        return ", ".join(self.get_spelling_set())

    #def getPrimaryCategory(self):
    #    if self.PrimaryCategory is not None:
    #        return self.PrimaryCategory
    #    self.PrimaryCategory = self.catrelationship_set.all()[0].Category.Label
    #    self.save()
    #    return self.PrimaryCategory
