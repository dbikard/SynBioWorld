
from datetime import datetime
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response
from django.template import RequestContext

import feedparser

def jobsRSS(request):
	items = feedparser.parse("http://www.nature.com/naturejobs/science/searches/20401930-all-synthetic-biology-jobs.rss")
	
	
	return render_to_response('jobs/jobs.html',
			{'items': items},
			context_instance=RequestContext(request))