#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
from handlers import append_path
from stream import StreamService
append_path()

import tornado.web,re
from xml.dom import minidom
from tornado import httpclient
from models import *
from unicodedata import normalize
from create.models import Causable
from spread.views import SocialHandler
from core.models import Profile
from StringIO import StringIO

class CollectionHandler(SocialHandler):
    def get(self):
        if not self.authenticated(): return
        self.render(self.templates()+'collection.html')

class FeedHandler(SocialHandler):
    def get(self):
        if not self.authenticated(): return
        service = StreamService()
        feed = service.top_rated()
        return self.render(self.templates()+'play.html',feed=feed)
    def post(self):
        token = self.parse_request(self.request.body)
        service = StreamService()
        feed = service.top_rated()
        return self.srender('play.html',feed=feed,token=token)

    
class UploadHandler(SocialHandler):
    def get(self):
        if not self.authenticated(): return
        description = ''; token = '!!'
        for k in self.request.arguments.keys(): description += '%s;;' % self.request.arguments[k][0]
        t = token.join(description[:-2].split())
        self.clear_cookie('description')
        self.set_cookie('description',t)
    def post(self):
        content = re.split(';;',self.get_cookie('description').replace('!!',' ').replace('"',''))
        title = '%s' % content[3]
        text = '%s' % content[0]; keys = ','
        keywords = content[1].split(' ')
        for k in keywords: k = normalize('NFKD',k.decode('utf-8')).encode('ASCII','ignore')
        keys = keys.join(keywords)
        print title,text,keys
        service = StreamService()
        response = service.video_entry(title,text,keys)
        video_io = StringIO()
        video = self.request.files['Filedata'][0]
        video_io.write(video['body'])
        resp = service.insert_video(response,video_io,video["content_type"])
        current_profile = Profile.objects.all().filter(user=self.current_user)[0]
        current_profile.points += 1
        current_profile.save()
        print resp
      
        return
        playable = Playable(user=self.current_user(),title='>'+title,description=text,token='teste')
        playable.save()
        self.redirect('/')

class ScheduleHandler(SocialHandler):
    def get(self):
        if "action" in self.request.arguments:
            play = Playable.objects.all().filter(user=self.current_user)
            cause = Causable.objects.all().filter(user=self.current_user)
            self.srender('action.html',play=play,cause=cause)
        else: 
            play = PlaySchedule.objects.all().filter(user=self.current_user)
            cause = CauseSchedule.objects.all().filter(user=self.current_user)
            message = ""
            if not len(play) and not len(cause):
                message = "Você não possui nenhuma programação no momento. Gostaria de criar uma?"
            else:
                scheds = len(PlaySchedule.objects.filter(user=self.current_user()).values('name').distinct())
                message = '%i Programações de vídeos disponíveis' % scheds
            self.srender('schedule.html',message=message)
    def post(self):
        playables = []
        objects = self.get_argument('objects')
        title = self.get_argument('title')
        objs = urllib.unquote_plus(str(objects)).split(',')
        for o in objs: playables.append(Playable.objects.all().filter(token=o)[0])
        for p in playables: 
            playsched = PlaySchedule(user=self.current_user(),play=p,name=title)
            playsched.save()
        scheds = len(PlaySchedule.objects.all().filter(user=self.current_user(),name=title))
        self.srender('schedule.html',message='%i Programações de vídeos disponíveis' % scheds)
