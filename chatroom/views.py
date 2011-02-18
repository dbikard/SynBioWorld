
from datetime import datetime
from django.conf import settings
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response
from django.template import RequestContext
from chatroom.models import chatRoom

from random import choice
from django.utils import simplejson
from google.appengine.api import channel, memcache


ANONYMOUS_IDS = set(range(1, 1000)) # you can increase it for accepting more anonymous users

def chatroom(request):
	room=chatRoom.objects.all()
	if not room:
		room=chatRoom(name="general chat",chat="")
		room.save()
	else:
		room=room[0]
	return direct_to_template(request,"chatroom/chatroom.html",{"text": room.chat})
	
def broadcast(message, tokens=None):
	if not tokens:
		tokens = memcache.get('tokens')
	if tokens:
		tokens.pop('_used_ids', None) # make sure you won't use the tokens after broadcast(), otherwise you need do a copy
		ids = set(tokens.values()) # remove duplicate ids
		# be noticed that a logged in user may connect to 1 channel by using several browsers at the same time
		# it works strange both in the cloud and local server:
		#   1. if removed the duplicate ids, only the last connected browser can receive the message
		#   2. if not removed them, all the browsers will receive duplicate messages
		# I don't know if it's a bug of the SDK 1.4.0
		for id in ids: # it may take a while if there are many users in the room, I think you can use task queue to handle this problem
			if isinstance(id, int):
				id = 'anonymous(%s)' % id
			channel.send_message(id, message)
		
		message_dic=eval(message)
		if "user" in message_dic.keys():
			room=chatRoom.objects.get(name="general chat")
			room.chat="<strong>"+message_dic["user"]+": </strong>"+message_dic["msg"]+"<br>" + room.chat
			room.save()

def GetToken(request):
	tokens = memcache.get('tokens') or {}
	user = request.user
	if user.is_authenticated():
		channel_id = id = user.email # you can use hash algorithm for ensuring the channel id is less then 64 bytes
	else:
		used_ids = tokens.get('_used_ids') or set()
		available_ids = ANONYMOUS_IDS - used_ids
		if available_ids:
			available_ids = list(available_ids)
		else:
			return HttpResponse('', mimetype='application/javascript')
		id = choice(available_ids)
		used_ids.add(id)
		tokens['_used_ids'] = used_ids
		channel_id = 'anonymous(%s)' % id
	token = channel.create_channel(channel_id)
	tokens[token] = id
	memcache.set('tokens', tokens) # you can use datastore instead of memcache
	response_dic={}
	response_dic['token']=token
	return HttpResponse(token, mimetype='application/javascript')

def ReleaseToken(request):
	if request.method == 'POST':
		token = request.POST.get('token')
		if not token:
			return HttpResponse('', mimetype='application/javascript')
		tokens = memcache.get('tokens')
		if tokens:
			id = tokens.get(token, '')
			if id:
				if isinstance(id, int):
					used_ids = tokens.get('_used_ids')
					if used_ids:
						used_ids.discard(id)
						tokens['_used_ids'] = used_ids
					user_name = 'anonymous(%s)' % id
				else:
					user_name = id.split('@')[0]
				del tokens[token]
				memcache.set('tokens', tokens)
				message = user_name + ' has left the chat room.'
				message = simplejson.dumps(message)
				broadcast(message, tokens)
		return HttpResponse('', mimetype='application/javascript')

def Open(request):
	if request.method == 'POST':
		token = request.POST.get('token')
		if not token:
			return HttpResponse('', mimetype='application/javascript')
		tokens = memcache.get('tokens')
		if tokens:
			id = tokens.get(token, '')
			if id:
				if isinstance(id, int):
					user_name = 'anonymous(%s)' % id
				else:
					user_name = request.user.username
				message = {'msg': user_name + u' has joined the chat room.'}
				message = simplejson.dumps(message)
				broadcast(message, tokens)
		return HttpResponse('', mimetype='application/javascript')
				
				
def Receive(request):
	if request.method == 'POST':
		token = request.POST.get('token', '')
		if not token:
			return HttpResponse('', mimetype='application/javascript')
		message = request.POST.get('content','')
		if not message:
			return HttpResponse('', mimetype='application/javascript')
		tokens = memcache.get('tokens')
		if tokens:
			id = tokens.get(token, '')
			if id:
				if isinstance(id, int):
					user_name = 'anonymous(%s)' % id
				else:
					user_name = request.user.username
				message = {'user': user_name, 'msg': message}
				message = simplejson.dumps(message)
				if len(message) > channel.MAXIMUM_MESSAGE_LENGTH:
					return HttpResponse('', mimetype='application/javascript')
				broadcast(message)
				
		return HttpResponse(message, mimetype='application/javascript')
				
