from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext

def index(request):
	return HttpResponseRedirect('/interclient/')
	# return render_to_response('index.html', {}, context_instance=RequestContext(request))