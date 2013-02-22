#!/usr/bin/python
# -*- coding: utf-8 -*-
from forms import CausesForm
from models import *
from coronae import append_path
from unicodedata import normalize 
append_path()

import urllib

from core.social import *
from core.views import *
from spread.models import Playable

def main(request):
    proj = Project()
    if request.method == 'GET':
        return proj.view_project(request)
    elif request.method == 'POST':
        return proj.create_project(request)
    
def grab(request):
    return response('Hello World!')

def link_project(request):
    proj = Project()
    if request.method == 'GET':
        return proj.link_project(request)

def init_create(request):
    c = Create()
    if request.method == 'GET':
        return c.view_create(request)
    elif request.method == 'POST':
        return c.donate_cause(request)

def movement(request):
    group = ProjectGroup()
    if request.method == 'GET':
        return group.view_movement(request)
    elif request.method == 'POST':
        return group.create_movement(request)

class Create(Efforia):
    def __init__(self): pass
    def view_create(self,request):
        if 'object' in request.GET:
            o,t = request.GET['object'][0].split(';')
            now,objs,rel = self.get_object_bydate(o,t)
            obj = globals()[objs].objects.all().filter(date=now)
            self.get_donations(obj)
        else: return render(request,"createapp.jade",{'static_url':settings.STATIC_URL},content_type='text/html')
    def donate_cause(self,request):
        u = self.current_user(request)
        value = int(request.POST['credits'][0])
        o,t = request.POST['object'][0].split(';')
        now,objs,rel = self.get_object_bydate(o,t)
        obj = globals()[objs].objects.all().filter(date=now)[0]
        don = CausableDonated(value=value,donator=u,cause=obj)
        don.save()
        donations = list(CausableDonated.objects.all().filter(cause=obj))
        return self.render_grid(donations,request)

class Project(Efforia,TwitterHandler):
    def __init__(self): pass
    def view_project(self,request):
        if 'view' in request.GET:
            strptime,token = request.GET['object'].split(';')
            now,obj,rel = self.get_object_bydate(strptime,token)
            spreaded = globals()[rel].objects.all().filter(date=now)[0]
            feed = []; feed.append(spreaded.spreaded)
            spreads = globals()[rel].objects.all().filter(spreaded=spreaded.spreaded)
            for s in spreads: feed.append(s.spread)
            self.render_grid(feed)
        else:
            return render(request,"project.jade",{},content_type='text/html')
    def create_project(self,request):
        u = self.current_user(request)
        n = t = e = ''; c = 0
        for k,v in request.POST.items():
            if 'title' in k: n = '#%s' % v.replace(" ","")
            elif 'credit' in k: c = int(v)
            elif 'content' in k: t = v
            elif 'deadline' in k: e = datetime.strptime(v,'%d/%m/%Y')
        project = Causable(name=n,user=u,content=t,end_time=e,credit=c)
        project.save()
        self.accumulate_points(1,request)
        return response('Project created successfully')
        #token = '%s' % request.POST['token']
        #video = Playable.objects.all().filter(token=token)[0]
    def link_project(self,request):
        #cause = Causable(name='#'+name,user=self.current_user(request),play=video,content=text,end_time=end_time,credit=credit)
        #cause.save()
        #causes = Causable.objects.all().filter(user=self.current_user(request)
        #return render(request,'grid.jade',{'f':causes},content_type='text/html')
        return response('Hello World!')

class ProjectGroup(Efforia):
    def __init__(self): pass
    def view_movement(self,request):
        u = self.current_user(request)
        if 'action' in request.GET:
            feed = []; a = Action('selection')
            a.href = 'movement'
            feed.append(a)
            causes = Causable.objects.all().filter(user=u)
            for c in causes:
                c.name = '%s#' % c.name 
                feed.append(c)
            return self.render_grid(feed,request)
        elif 'view' in request.GET:
            move = Movement.objects.all(); feed = []; count = 0
            if 'grid' in request.GET['view']:
                for m in move.values('name').distinct():
                    if not count: 
                        a = Action('new')
                        a.href = 'movement?action=grid'
                        feed.append(a)
                    feed.append(move.filter(name=m['name'],user=u)[0])
                    count += 1
            else:
                name = '#%s' % request.GET['title'].rstrip()
                feed.append(Action('play'))
                for m in move.filter(name=name,user=u): feed.append(m.cause)
            return self.render_grid(feed,request)
        else: 
            move = Movement.objects.all().filter(user=u)
            message = ""
            if not len(move): message = "Você não possui nenhum movimento. Gostaria de criar um?"
            else:
                scheds = len(Movement.objects.filter(user=u).values('name').distinct())
                message = '%i Movimentos em aberto' % scheds
            return render(request,'movement.jade',{
                                                  'message':message,
                                                  'tutor':'Os movimentos são uma forma fácil de acompanhar todos os projetos do Efforia em que você apoia. Para utilizar, basta selecioná-los e agrupá-los num movimento.'
                                                  })
    def create_movement(self,request):
        u = self.current_user(request)
        causables = []
        objects = request.POST['objects']
        title = request.POST['title']
        objs = urllib.unquote_plus(objects).split(',')
        for o in objs: 
            ident,token = o.split(';'); token = token[:1]
            obj,rels = self.object_token(token)
            causables.append(globals()[obj].objects.filter(id=ident)[0])
        for c in causables: 
            move = Movement(user=u,cause=c,name='##'+title)
            move.save()
        self.accumulate_points(1,request)
        moves = len(Movement.objects.all().filter(user=u).values('name').distinct())
        return render(request,'message.html',{
                                              'message':'%i Movimentos em aberto' % moves,
                                              'visual':'crowd.png',
                                              'tutor':'Os movimentos são uma forma fácil de acompanhar todos os projetos do Efforia em que você apoia. Para utilizar, basta selecioná-las e agrupá-las num movimento.'
                                              },content_type='text/html')
