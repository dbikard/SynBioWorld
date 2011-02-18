from .models import Paper, Person, Journal, Institution, Country, Town, Citation, Authorship, Affiliation
from datetime import datetime
from django.conf import settings
from django.contrib.syndication.views import Feed
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.simple import direct_to_template
from django.template import RequestContext
from .forms import SearchForm, addPapersForm
import re
from django.core.exceptions import ObjectDoesNotExist
from data_utils import update_SBW, cleanUnivName, parse_ISI_data, get_cited_paper
from google.appengine.api import taskqueue


#~ def search(request):
	#~ if request.method == 'POST':
		#~ form=SearchForm(request.POST)
		#~ if form.is_valid():
			#~ cla=form.cleaned_data['cla']
			#~ search=form.cleaned_data['search']
			
			#~ if cla=="Person":
				#~ search=re.findall("\w\w\w+",search)
				#~ if len(search)==1:
					#~ search=search[0].capitalize()
					#~ people=Person.objects.filter(last_name=search)
				#~ elif len(search)==2:
					#~ search.sort(lambda x,y: cmp(len(x),len(y)))
					#~ a,b=search
					#~ b=b.capitalize()
					#~ if len(a)<3:
						#~ a=a.upper()
						#~ people=Person.objects.filter(last_name=b).filter(initial=a)
					#~ else:
						#~ a=a.capitalize()
						#~ people=Person.objects.filter(last_name=b).filter(first_name=a)
						#~ if not people:
							#~ people=Person.objects.filter(last_name=a).filter(first_name=b)
					
				#~ return object_list(request, people, paginate_by=20)
			#~ if cla=="Institution":
				#~ return object_list(request, Institution.objects.filter(name__iexact=search), paginate_by=20)
			#~ if cla=="Paper":
				#~ return object_list(request, Paper.objects.filter(title__icontains=search), paginate_by=20)
		

def librarian_home(request):
	return direct_to_template(request,'librarian/home.html')

def list_people(request):
	des="Ordered by number of citation from SB papers."
	query=Person.objects.order_by('-sbw')
	return object_list(request, query, paginate_by=20, extra_context={'description':des,'total':query.count()})

def show_person(request, person_id):
	return object_detail(request, Person.objects.all(), person_id)
	
def list_paper(request,list_type):
	if list_type=="best":
		query= Paper.objects.order_by('-sbw')
		des="Ordered by number of citations from other SB papers."
	elif list_type=="recent":
		des="Recent publications from the top10 SB journals."
		best_journals=Journal.objects.order_by('-sbw').values_list('pk',flat=True)[:10]
		best_journals=map(int,best_journals)
		query=Paper.objects.filter(journal__in=best_journals,pubYear=datetime.now().year).order_by('-pubMonth')
	
	#elif list_type=="hotest":
	#	des="Papers the most cited during the previous year"
		
	
	return object_list(request,query, paginate_by=20,extra_context={'description':des,
												   'total':query.count(),
												   'list_type':list_type})

	
def show_paper(request, paper_id):
	return object_detail(request, Paper.objects.all(), paper_id)

def list_journal(request):
	des="Ordered by number of citations from SB papers."
	query=Journal.objects.order_by('-sbw')
	return object_list(request, query, paginate_by=20,extra_context={'description':des,'total':query.count()})

def show_journal(request, key):
	return object_detail(request, Journal.objects.all(), key)
	
def list_institution(request):
	des="Ordered by number of citations from SB papers."
	query=Institution.objects.order_by('-sbw')
	return object_list(request, query, paginate_by=20,extra_context={'description':des,'total':query.count()})

def show_institution(request, key):
	return object_detail(request, Institution.objects.all(), key)
	
def list_country(request):
	des="Ordered by importance in the synthetic biology field."
	return object_list(request, Country.objects.filter(has_SB=True).order_by('-sbw'), paginate_by=20,extra_context={'description':des})

def show_country(request, key):
	return object_detail(request, Country.objects.all(), key)

def import_ISI_data(request):
	if request.method=='POST':
		data=request.POST['data']
	
		new_papers=[]
		already_in_DB=[]
		pubdata=pubdata.split('\t')
		paper, created=parse_ISI_data(pubdata)
		if created:
			new_papers.append(paper)
		else:
			already_in_DB.append(paper)
		
		        			
		####################### Citations #####################################
		
		for new_paper in new_papers:
			CR=new_paper.raw_citations
			CR=CR.split(";")
			for cit in CR:
				cited_paper=get_cited_paper(cit)
				if cited_paper:
					new_citation=Citation(cited_paper=cited_paper,citing_paper=new_paper)
					new_citation.save()

def update_SBW_view(request):
	update_SBW()
	
def add_papers(request):
	if request.method == 'POST':
		form=addPapersForm(request.POST)

		if form.is_valid():
			data=form.cleaned_data['ISIdata']
			data=data.split('\r\n')[1:]
			for pubdata in data:
				PT,AU,BA,ED,GP,AF,CA,TI,SO,SE,LA,DT,CT,CY,CL,SP,HO,DE,ID,AB,C1,RP,EM,FU,FX,CR,NR,TC,PU,PI,PA,SN,BN,DI,J9,JI,PD,PY,VL,IS,PN,SU,SI,BP,EP,AR,DI2,PG,SC,GA,UT = pubdata.split('\t')
				reduced_data='\t'.join([AU,SO,TI, PD, VL, AB, DI, CR, PY, C1, EM])	
				taskqueue.add(url='/librarian/import_ISI_data', params={'data': reduced_data})
			
			taskqueue.add(url='/librarian/update_SBW')
			
			new_papers=[]
			already_in_DB=[]
			return  render_to_response('librarian/add_complete.html',{'new_papers': new_papers, 'already_in_DB': already_in_DB},context_instance=RequestContext(request))

	else:
		form = addPapersForm()
	
	return render_to_response('librarian/add_papers.html', {'form': form},context_instance=RequestContext(request))
	