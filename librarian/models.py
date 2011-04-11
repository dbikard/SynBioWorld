from .utils import slugify
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.sitemaps import Sitemap
from django.db import models
from django.db.models import permalink
from minicms.models import BaseContent
from random import choice
from string import ascii_letters, digits
from django.core.exceptions import ObjectDoesNotExist
from google.appengine.api import taskqueue
import re
import urllib2

def get_page(url):
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    html = response.read()
    response.close()
    return html

def uniquify(seq, idfun=None):  
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result
    
class Country(models.Model):
    name=models.CharField(max_length=200)
    sbw=models.IntegerField(null=True)
    has_SB=models.BooleanField()
    
    def __unicode__(self):
        return '%s' % (self.name)
        
    def get_institutions(self):
        return Institution.objects.filter(country=self).order_by('-sbw')

    def get_SBW(self):
	self.sbw=sum([inst.sbw for inst in self.get_institutions()])
	self.save()
	return self.sbw

class Town(models.Model):
    name=models.CharField(max_length=200)
    country=models.ForeignKey(Country)
    
    def __unicode__(self):
        return '%s' % (self.name)

class Institution(models.Model):
    name=models.CharField(max_length=200)
    country=models.ForeignKey(Country,null=True)
    sbw=models.IntegerField(null=True)
    
    def __unicode__(self):
        return '%s' % (self.name)
    
    def get_present_employee(self):
        aff=Affiliation.objects.filter(institution=self).order_by('-year')
        people=uniquify([x.employee for x in aff if x.employee.get_institution() == self])
	people.sort(cmp=lambda x,y: cmp(y.sbw,x.sbw))
        return people
    
    def get_past_employee(self):
        aff=Affiliation.objects.filter(institution=self).order_by('-year')
        people=uniquify([x.employee for x in aff if x.employee.get_institution() != self])
	people.sort(cmp=lambda x,y: cmp(y.sbw,x.sbw))
        return people
        
    def get_SBW(self):
	self.sbw=sum([scientist.sbw for scientist in self.get_present_employee()])
	self.save()
	return self.sbw

#~ class Keyword(models.Model):
    #~ name=models.CharField(max_length=200)
    #~ count=models.IntegerField(null=True)
    
    #~ def __unicode__(self):
        #~ return 'Keyword: %s' % (self.name)

class Person(models.Model):
    first_name=models.CharField(max_length=200,null=True)
    initials=models.CharField(max_length=10)
    last_name=models.CharField(max_length=200)
    email=models.CharField(max_length=200,null=True)
    sbw=models.IntegerField(null=True)
    
    def __unicode__(self):
        return "%s %s" % (self.last_name, self.initials)
    
    def get_papers(self):
        authorship_set=Authorship.objects.filter(author=self)
        paper_set=[x.paper for x in authorship_set]
	paper_set.sort(cmp=lambda x,y: cmp(y.pubYear,x.pubYear))
        return paper_set
    
    def get_institution(self):
	try:
            aff=Affiliation.objects.filter(employee=self).order_by('-year')[0]
            inst=aff.institution
	except:
	    inst=None
        return inst

    def get_SBW(self):
	self.sbw=sum([pub.sbw for pub in self.get_papers()])
	self.save()
	return self.sbw
    
    @permalink
    def get_absolute_url(self):
        return ('librarian.views.show_person', (),
                {'person_id': self.pk})

class Journal(models.Model):
    name=models.CharField(max_length=200,null=True)
    short_name=models.CharField(max_length=100,null=True)
    sbw=models.IntegerField(null=True)

    def get_name(self):
        if self.name and not self.short_name:
            L=self.name[0]
            num=re.match("[0-9]",L)
            if num:
                L="0-9"
            html = get_page("http://images.isiknowledge.com/WOK46/help/WOS/"+L+"_abrvjt.html")
            q=re.findall("<DT>(?P<name>.+)\n<B><DD>\t(?P<short_name>.+)\n</B>",html)
            names={}
            for n in q:
                names[n[0].capitalize()]=n[1].capitalize()

            if self.name in names.keys():
                self.short_name=names[self.name]
            else:
                self.short_name=self.name
                
            self.save()

        elif self.short_name and not self.name:
            L=self.short_name[0]
            num=re.match("[0-9]",L)
            if num:
                L="0-9"
            html = get_page("http://images.isiknowledge.com/WOK46/help/WOS/"+L+"_abrvjt.html")
            q=re.findall("<DT>(?P<name>.+)\n<B><DD>\t(?P<short_name>.+)\n</B>",html)
            short_names={}
            for n in q:
                short_names[n[1].capitalize()]=n[0].capitalize()

            if self.short_name in short_names.keys():
                self.name=short_names[self.short_name]
            else:
                self.name=self.short_name
                
            self.save()
            
    def __unicode__(self):
        return '%s' % (self.name)
    
    def get_papers(self):
        return Paper.objects.filter(journal=self).order_by('-pubYear')

    def get_SBW(self):
	self.sbw=sum([pub.sbw for pub in self.get_papers()])
	self.save()
	return self.sbw


class Raw_cit(models.Model):
    cit=models.CharField(max_length=200,null=True)
    last_name=models.CharField(max_length=50, null=True)
    init=models.CharField(max_length=5, null=True)
    year=models.IntegerField(null=True)
    jour=models.ForeignKey(Journal, null=True)
    vol=models.CharField(max_length=20, null=True)
    page=models.CharField(max_length=20, null=True)
    doi=models.CharField(max_length=100, null=True)

    def get_paper(self):
        cited_paper=Paper.objects.filter(raw_cit=self)
        if len(cited_paper)==1:
            return cited_paper[0]
        else:
            if self.doi:
                cited_paper=Paper.objects.filter(doi=self.doi)
            else:
                try:
                    cited_first_au=Person.objects.get(last_name=self.last_name, initials=self.init)
                except ObjectDoesNotExist:
                    cited_first_au=None

                cited_paper=Paper.objects.filter(journal=self.jour)
                
                if cited_first_au:
                    cited_paper=cited_paper.filter(first_au=cited_first_au)
                    if self.year:
                        cited_paper=cited_paper.filter(pubYear=self.year)

                    if self.vol:
                        cited_paper=cited_paper.filter(volume=self.vol)

                    cited_paper=cited_paper.filter(volume=self.vol)

                    cited_paper=list(cited_paper)
                    if len(cited_paper)==1:
                        cited_paper=cited_paper[0]
                        cited_paper.raw_cit=self
                        cited_paper.save()
                        return cited_paper

                
class Paper(models.Model):
    first_au = models.ForeignKey(Person,null=True)
    title = models.CharField(max_length=200, null=True)
    journal =  models.ForeignKey(Journal,null=True)
    volume=models.CharField(max_length=10,null=True)
    page=models.CharField(max_length=10,null=True)
    pubMonth=models.IntegerField(null=True)
    pubYear=models.IntegerField(null=True)
    abstract=models.TextField(null=True)
    doi=models.CharField(max_length=200,null=True)
    sbw=models.IntegerField(null=True)
    raw_citations=models.TextField(max_length=100000,null=True)
    raw_cit=models.ForeignKey(Raw_cit,null=True)

    def __unicode__(self):
        return self.title
    
    def get_authors(self):
        authorship_set=Authorship.objects.filter(paper=self).order_by('position')
        author_set=[x.author for x in authorship_set]
        return author_set

    def get_SBW(self):
        self.sbw=Citation.objects.filter(cited_paper=self).count()
	self.save() 
	return self.sbw

    def update_citations(self):
        CR=self.raw_citations
        CR=CR.split(";")
        for cit in CR:
                cit=cit.strip()
                taskqueue.add(url='/librarian/update_raw_cit/', params={'pk': self.pk,'raw_cit':cit})

class Citation(models.Model):
    citing_paper=models.ForeignKey(Paper, related_name="citing_set")
    cited_paper=models.ForeignKey(Paper, related_name="cited_set",null=True)

    def __unicode__(self):
        return '%s-%s cited by %s-%s' % (self.cited_paper.first_au.last_name, self.cited_paper.pubYear, self.citing_paper.first_au.last_name,self.citing_paper.pubYear)
    
class Authorship(models.Model):
    author = models.ForeignKey(Person)
    paper = models.ForeignKey(Paper)
    position = models.IntegerField(null=True)
    
    def __unicode__(self):
        return "%s-%s" % (self.author.last_name,self.paper.title)

class Affiliation(models.Model):
    institution=models.ForeignKey(Institution)
    employee=models.ForeignKey(Person)
    year=models.IntegerField(null=True)
    
#~ class Person_has_keyword(models.Model):
    #~ person=models.ForeignKey(Person)
    #~ keyword=models.ForeignKey(Keyword)
    #~ count=models.IntegerField(null=True)
    
class ISI_data(models.Model):
    data=models.TextField(null=True)

class PeopleSitemap(Sitemap):
    changefreq = "never"

    def items(self):
        return Person.objects.all()
