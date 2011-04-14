from .models import Paper, Person, Journal, Institution, Country, Town, Citation, Authorship, Affiliation, ISI_data, Raw_cit
from datetime import datetime
from django.conf import settings
from django.contrib.syndication.views import Feed
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.list_detail import object_list, object_detail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic.simple import direct_to_template
from django.template import RequestContext
from .forms import SearchForm, addPapersForm
import re
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from data_utils import cleanUnivName, parse_ISI_data, parse_ISI_data2, ISIquery
from google.appengine.api import taskqueue
from google.appengine.ext import deferred
from django.contrib.auth.decorators import login_required
		

def librarian_home(request):
	best_journals=Journal.objects.order_by('-sbw').values_list('pk',flat=True)[:20]
	best_journals=map(int,best_journals)
	query=Paper.objects.filter(journal__in=best_journals,pubYear=datetime.now().year).order_by('-pubMonth')
        top_query=Paper.objects.order_by('-sbw')[:5]
        best_journals=Journal.objects.order_by('-sbw').values_list('pk',flat=True)[:20]
	best_journals=map(int,best_journals)
	recent_query=Paper.objects.filter(journal__in=best_journals,pubYear=datetime.now().year).order_by('-pubMonth')[:5]
	return render_to_response('librarian/home.html', {'top': top_query,'recent':recent_query},context_instance=RequestContext(request))


def list_people(request):
	des="Ordered by number of citation from SB papers."
	query=Person.objects.order_by('-sbw')
	paginator = Paginator(query, 20) # Show 20 contacts per page

        page = request.GET.get('page')
        if not page:
                page=1
        try:
                objects = paginator.page(page)
        except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                objects = paginator.page(1)
        except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                objects = paginator.page(paginator.num_pages)

        return render_to_response('librarian/person_list.html', {'description':des, 'total': paginator.count, 'objects': objects}, context_instance=RequestContext(request))
	
def show_person(request, person_id):
	return object_detail(request, Person.objects.all(), person_id)
	
def list_paper(request,list_type):
	if list_type=="best":
		query= Paper.objects.order_by('-sbw')
		des="Ordered by number of citations from other SB papers."
	elif list_type=="recent":
		des="Recent publications from the top20 SB journals."
		best_journals=Journal.objects.order_by('-sbw').values_list('pk',flat=True)[:20]
		best_journals=map(int,best_journals)
		query=Paper.objects.filter(journal__in=best_journals,pubYear=datetime.now().year).order_by('-pubMonth')
	elif list_type=="hot":
		query=Paper.objects.filter(pubYear=datetime.now().year).order_by('-pubMonth')[:100]
		hot_papers=[]	
		score={}
		for new_paper in query:	
			CR=new_paper.raw_citations
			CR=CR.split(";")
			for cit in CR:
				cited_paper=get_cited_paper(cit)
				if cited_paper:
					if cited_paper in hot_papers:
						score[cited_paper]+=1
					else:
						hot_papers.append(cited_paper)
						score[cited_paper]=1
		
		hot_papers.sort(cmp=lambda x,y: cmp(score[y],score[x]))
		query=filter(lambda x: score[x]>1,hot_papers)
	#elif list_type=="hotest":
	#	des="Papers the most cited during the previous year"
		
	
	paginator = Paginator(query, 20) # Show 20 contacts per page

        page = request.GET.get('page')
        if not page:
                page=1
        try:
                objects = paginator.page(page)
        except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                objects = paginator.page(1)
        except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                objects = paginator.page(paginator.num_pages)

        return render_to_response('librarian/paper_list.html', {'description':des, 'total': paginator.count, 'list_type':list_type, 'objects': objects}, context_instance=RequestContext(request))
								   

	
def show_paper(request, paper_id):
	return object_detail(request, Paper.objects.all(), paper_id)

def list_journal(request):
	des="Ordered by number of citations from SB papers."
	query=Journal.objects.order_by('-sbw')
	paginator = Paginator(query, 20) # Show 20 contacts per page

        page = request.GET.get('page')
        if not page:
                page=1
        try:
                objects = paginator.page(page)
        except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                objects = paginator.page(1)
        except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                objects = paginator.page(paginator.num_pages)

        return render_to_response('librarian/journal_list.html', {'description':des, 'total': paginator.count, 'objects': objects}, context_instance=RequestContext(request))

def show_journal(request, key):
	return object_detail(request, Journal.objects.all(), key)
	
def list_institution(request):
	des="Ordered by number of citations from SB papers."
	query=Institution.objects.order_by('-sbw')
	paginator = Paginator(query, 20) # Show 20 contacts per page

        page = request.GET.get('page')
        if not page:
                page=1
        try:
                objects = paginator.page(page)
        except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                objects = paginator.page(1)
        except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                objects = paginator.page(paginator.num_pages)

        return render_to_response('librarian/institution_list.html', {'description':des, 'total': paginator.count, 'objects': objects}, context_instance=RequestContext(request))

def show_institution(request, key):
	return object_detail(request, Institution.objects.all(), key)
	
def list_country(request):
	des="By order of importance in the synthetic biology field."
	query=Country.objects.filter(has_SB=True).order_by('-sbw')
	paginator = Paginator(query, 20) # Show 20 contacts per page
        page = request.GET.get('page')
        if not page:
                page=1
        try:
                objects = paginator.page(page)
        except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                objects = paginator.page(1)
        except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                objects = paginator.page(paginator.num_pages)

        return render_to_response('librarian/country_list.html', {'description':des, 'total': paginator.count, 'objects': objects}, context_instance=RequestContext(request))
	return object_list(request, query, paginate_by=20,extra_context={'description':des})

def show_country(request, key):
	return object_detail(request, Country.objects.all(), key)




def import_ISI_data(request):
	if request.method=='POST':
		pk=int(request.POST['pk'])
		data=ISI_data.objects.get(pk=pk)
		pubdata=data.data
		pubdata=pubdata.split('\t')
		new_paper, created=parse_ISI_data(pubdata)
		
		if created:
                        taskqueue.add(url='/librarian/update_citation/',
                                      params={'pk': new_paper.pk},
                                      queue_name="citationsUpdate",
                                      name=str(new_paper.pk))

                data.delete()

	return HttpResponse('done')

def update_ISI_data(request):
        if request.method=='POST':
		pk=int(request.POST['pk'])
		data=ISI_data.objects.get(pk=pk)
		pubdata=data.data
		pubdata=pubdata.split('\t')
		parse_ISI_data2(pubdata)
                data.delete()

	return HttpResponse('done')

def update_citation(request):
        pk=int(request.POST['pk'])
        paper=Paper.objects.get(pk=pk)
        paper.update_citations()
        return HttpResponse('done')

def update_journal(request):
        pk=int(request.POST['pk'])
        jour=Journal.objects.get(pk=pk)
        jour.get_name()
        return HttpResponse('done')

@login_required			
def update_citations(request):
        pks=Paper.objects.exclude(title=None).values_list('pk',flat=True)
	for p in pks:
                taskqueue.add(url='/librarian/update_citation/', params={'pk': p})

        return HttpResponse('done')


def update_SBW_entity(request):
        pk=int(request.POST['pk'])
        classes={'Paper':Paper, 'Person':Person, 'Journal':Journal, 'Institution':Institution, 'Country':Country} 
        cl=classes[request.POST['cl']]
        entity=cl.objects.get(pk=pk)
        entity.get_SBW()
        return HttpResponse('done')
        
@login_required
def update_SBW_view(request,cl):
        classes={'Paper':Paper, 'Person':Person, 'Journal':Journal, 'Institution':Institution, 'Country':Country}      
        c=classes[cl]
        ran=request.GET.get('range')
        if ran:
                ran=int(ran)
                pks=c.objects.all().values_list('pk',flat=True)[ran*1000:(ran+1)*1000]
        else:
                pks=c.objects.all().values_list('pk',flat=True)
                
	for p in pks:
                taskqueue.add(url='/librarian/update_SBW_entity/', params={'pk': p, 'cl':cl})

        return HttpResponse('done')


def import_state(request):
	count=str(ISI_data.objects.all().count())
	return HttpResponse(count, mimetype='text/plain')

@login_required
def add_progress(request):
	return render_to_response('librarian/add_progress.html',context_instance=RequestContext(request))

@login_required
def add_papers(request):
	if request.method == 'POST':
		form=addPapersForm(request.POST)
                
		if form.is_valid():
                        data=form.cleaned_data['ISIdata']
                        data=data.split('\r\n')[1:]
                        if 'Update' in request.POST:
                                for pubdata in data:
                                        isi=ISI_data(data=pubdata)
                                        isi.save()
                                        taskqueue.add(url='/librarian/update_ISI_data/', params={'pk': isi.pk})
                                        
                                return HttpResponse('coucou', mimetype='text/plain')
                        elif 'Import' in request.POST:
                                for pubdata in data:
                                        isi=ISI_data(data=pubdata)
                                        isi.save()
                                        taskqueue.add(url='/librarian/import_ISI_data/', params={'pk': isi.pk})

                                return  render_to_response('librarian/add_progress.html',context_instance=RequestContext(request))

	else:
		form = addPapersForm()
	
	return render_to_response('librarian/add_papers.html', {'form': form},context_instance=RequestContext(request))
	
@login_required
def to_import(request):
        paps=Paper.objects.filter(title=None).order_by('-sbw')[:100]
        resp=''
        cits=[]
        for p in paps:
                cits.append([p.raw_cit.cit,p.sbw])
                resp+=str(p.sbw)+"\t"+p.raw_cit.cit+'\n'

        resp+="\n============= ISI query =================\n"
        for i in range(len(cits)//10-1):
                resp+=ISIquery(range(i*10,(i+1)*10),cits)+'\n'
        
        return HttpResponse(resp, mimetype='text/plain')

prog = re.compile("(?P<last_name>\w+)[.\s](?P<init>\w+)(?:,\s)?(?P<year>\d+)?(?:,\s)(?P<journal>(?:[\s-]?\w+)+)(?:,\s)?(?P<vol>V\d+)?(?:,\s)?(?P<page>[PE]\d+)?(?:,\s)?(?P<doi>DOI .+$)?",re.UNICODE)
def update_raw_cit(request):
        pk=int(request.POST['pk'])
        paper=Paper.objects.get(pk=pk)
        cit=request.POST['raw_cit']
        m=prog.match(cit)
        if m:
                last_name,init,year,journal,vol,page,doi=m.groups()
                if last_name and year and journal:
                        raw_cit=None
                        if doi:
                                doi=doi[4:]
                                try:
                                        raw_cit=Raw_cit.objects.get(doi=doi)
                                except:
                                        pass

                        if not raw_cit:
                                year=int(year)
                                if vol:
                                        vol=vol[1:]
                                

                                cited_jour, created=Journal.objects.get_or_create(short_name=journal.capitalize())

                                if created:
                                    taskqueue.add(url='/librarian/update_journal/',
                                              params={'pk': cited_jour.pk},
                                              queue_name="journal")

                                #In case there is some differences between citations of the same paper, we need to find the right one
                                raw_cit_list=Raw_cit.objects.filter(last_name=last_name,jour=cited_jour,year=year)
                                raw_cit_list=list(raw_cit_list)
                                for xcite in raw_cit_list:
                                        if xcite.vol and vol:
                                            if xcite.vol!=vol:
                                                raw_cit_list.remove(xcite)
                                                continue
                                        if xcite.page and page:
                                            if xcite.page!=page:
                                                raw_cit_list.remove(xcite)
                                                continue

                                if len(raw_cit_list)==1:
                                        raw_cit=raw_cit_list[0]
                                        
                                #if no corresponding raw_cit is found, create a new one
                                if not raw_cit:
                                    raw_cit=Raw_cit(cit=cit,
                                                    last_name=last_name.capitalize(),
                                                    init=init,
                                                    year=year,
                                                    jour=cited_jour,
                                                    vol=vol,
                                                    page=page,
                                                    doi=doi)

                        cited_paper=raw_cit.get_paper()
                        #if nothing is found, creates a new Paper objects associated to the raw_cit
                        if not cited_paper:
                                cited_paper=Paper(raw_cit=raw_cit)
                                cited_paper.save()

                        cit,created=Citation.objects.get_or_create(cited_paper=cited_paper,citing_paper=paper)

        return HttpResponse('done')


        
