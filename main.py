import cgi, os, sys, re

sys.path.insert(0, "lib")

import PIL
from datetime import date

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import images

import twitter as twapi
from twitpicapi import get_twitpic_image

from twitter_oauth_handler import *
#import PIL

from models import Moustache, get_random_taches, Vote, get_top_taches, get_bottom_taches, get_spider, Spider, get_taches_by_username

class MainPage(webapp.RequestHandler):
    def get(self):
        template_values = self.auth_and_taches()
        self.to_template(template_values)
        
    def to_template(self, template_values):
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_values))
        
    def auth_and_taches(self):
        client = OAuthClient("twitter", self)
        logged_in = client.get_cookie()
        
        extra = {}
        if logged_in:
            info = client.get("/account/verify_credentials")
            extra.update(info)
            rate_info = client.get("/account/rate_limit_status")
            extra["rate_info"] = rate_info
        
        tache1, tache2 = get_random_taches()
        
        template_values = {
            "pagetitle": 'Welcome to Moustache Wars',
            "logged_in": logged_in,
            "tache1": tache1,
            "tache2": tache2,
        }
        template_values.update(extra)
        return template_values
        
    def post(self):
        loser = db.get(str(self.request.get('loser')))
        winner = db.get(str(self.request.get('winner')))
        vote = Vote(winner=winner, loser=loser)
        vote.put()
        
        #Wins and losses
        loser.losses = loser.losses+1
        loser.win_percentage = loser.calc_win_percentage()
        winner.wins = winner.wins+1
        winner.win_percentage = winner.calc_win_percentage()
        loser.put()
        winner.put()
        
        extra_values = {}
        extra_values['last_winner'] = winner
        extra_values['last_loser'] = loser
        
        template_values = self.auth_and_taches()
        template_values.update(extra_values)
        self.to_template(template_values)
        
class Top10(webapp.RequestHandler):
    def get(self):
        taches = get_top_taches()
        template_values = {
            'page-title': 'Top 10 Taches',
            'taches': taches,
            'ranking_type': 'Top',
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/topbottom.html')
        self.response.out.write(template.render(path, template_values))

class AllTaches(webapp.RequestHandler):
    def get(self):
        taches = Moustache.all().order('-created').fetch(30)
        template_values = {
            'pagetitle': 'Bottom 10 Taches',
            'taches': taches,
            'ranking_type': 'Bottom',
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/topbottom.html')
        self.response.out.write(template.render(path, template_values))    

class Bottom10(webapp.RequestHandler):
    def get(self):
        taches = get_bottom_taches()
        template_values = {
            'pagetitle': 'Bottom 10 Taches',
            'taches': taches,
            'ranking_type': 'Bottom',
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/topbottom.html')
        self.response.out.write(template.render(path, template_values))       

class Profile(webapp.RequestHandler):
    def get(self, username):
        taches = get_taches_by_username(username)
        template_values = {
            'page-title': 'Top 10 Taches',
            'taches': taches,
            'ranking_type': 'Top',
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/topbottom.html')
        self.response.out.write(template.render(path, template_values))
        


today = date.today()

class GrabTwitter(webapp.RequestHandler):
    def get(self):
        spider = get_spider()
        if not spider:
            spider = Spider()
            spider.put()
            
        twitpic_spider_list = spider.twitpics
        
        twitter_search = twapi.Twitter(domain="search.twitter.com")
        twitter_search.encoded_args = 'q=&ands=&phrase=twitpic&ors=%23movember+%23mowars&since=' + str(spider.last_since) + '&rpp=100&until=' + str(spider.last_until)
        x = twitter_search.search()
        
        reg = re.compile(r'http://(www)?twitpic.com/([^\s]*)\s*', re.I)
        results = []
        
        for twt in x['results']:
                res = reg.findall(twt['text'])
            
                for url_groups in res:
                    dict = {
                        'name': twt['from_user'],
                        'message': twt['text'],
                        'img_url': url_groups[1],
                    }

                    tache = Moustache()
                    tache.name = dict['name']
                    tache.tweet = dict['message']
                    tache.twitpic = dict['img_url']
                    
                    if dict['img_url'] not in twitpic_spider_list:
                        try:
                            tache_image = images.resize(get_twitpic_image(dict['img_url']), 400, 400)
                            tache.image = db.Blob(tache_image)
                            tache.put()
                            twitpic_spider_list.append(dict['img_url'])
                            results.append(dict)
                        except:
                            pass
        
        spider.last_since = spider.last_until
        new_until = spider.last_until + timedelta(days=1)
        if new_until<=today:
            spider.last_until = new_until
        else:
            spider.last_until = today
        spider.twitpics = twitpic_spider_list
        spider.put()
        spider = get_spider()
        self.response.out.write(str(spider.twitpics))

class Upload(webapp.RequestHandler):
  def post(self):
    client = OAuthClient("twitter", self)
    logged_in = client.get_cookie()
    if not logged_in:
      self.redirect("/")
      
    info = client.get("/account/verify_credentials")
    
    tache = Moustache()

    #if users.get_current_user():
    #  greeting.author = users.get_current_user()

    if self.request.get('add-tache'):
      tache.name = info["screen_name"]
      tache_image = images.resize(self.request.get('image'), 400, 400)
      tache.image = db.Blob(tache_image)
      tache.put()
      self.redirect('/')
    else:
      self.render_form()
      
  def get(self):
    client = OAuthClient("twitter", self)
    logged_in = client.get_cookie()
    if not logged_in:
      # TODO: Tell them they need to login + link to Twitter login.
      self.redirect("/")

    self.render_form()
    
  def render_form(self):
    template_values = {
      'pagetitle': 'Upload a new tache',
    }
    path = os.path.join(os.path.dirname(__file__), 'templates/upload.html')
    self.response.out.write(template.render(path, template_values))

class Image (webapp.RequestHandler):
  def get(self):
    tache_id = self.request.get("img_id")
    tache = db.get(tache_id)
    
    if tache.image:
      self.response.headers['Content-Type'] = "image/jpg"
      self.response.out.write(tache.image)
    else:
      self.error(404)

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/upload', Upload),
                                      ('/img', Image),
                                      ('/tachewin', Top10),
                                      ('/tachefail', Bottom10),
                                      ('/grabtwitter', GrabTwitter),
                                      ('/profile/(.*)', Profile),
                                      #('/all', AllTaches),
                                      # Logins
                                      ('/oauth/(.*)/(.*)', OAuthHandler)
                                     ],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()