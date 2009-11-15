import cgi, os, sys

sys.path.insert(0, "lib")

import PIL

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import images


from twitter_oauth_handler import *
#import PIL

from models import Moustache, get_random_taches, Vote

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
        winner.wins = winner.wins+1
        loser.put()
        winner.put()
        
        extra_values = {}
        extra_values['last_winner'] = winner
        extra_values['last_loser'] = loser
        
        template_values = self.auth_and_taches()
        template_values.update(extra_values)
        self.to_template(template_values)
        


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
                                      # Logins
                                      ('/oauth/(.*)/(.*)', OAuthHandler)
                                     ],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()