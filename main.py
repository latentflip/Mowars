import cgi, os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import images

import sys
sys.path.insert(0, "lib")
from twitter_oauth_handler import *

from models import Moustache
#from views import Image

class MainPage(webapp.RequestHandler):
    def get(self):
        client = OAuthClient("twitter", self)
        logged_in = client.get_cookie()
        
        extra = {}
        if logged_in:
            info = client.get("/account/verify_credentials")
            extra.update(info)
            rate_info = client.get("/account/rate_limit_status")
            extra["rate_info"] = rate_info
        
        template_values = {
            "pagetitle": 'Welcome to Moustache Wars',
            "logged_in": logged_in,
        }
        template_values.update(extra)
        
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_values))

class Upload(webapp.RequestHandler):
  def post(self):
    tache = Moustache()

    #if users.get_current_user():
    #  greeting.author = users.get_current_user()

    if self.request.get('add-tache'):
      tache.name = self.request.get('name')
      avatar = images.resize(self.request.get("image"), 32, 32)
      tache.image = db.Blob(tache_image)
      tache.put()
      self.redirect('/')
    else:
      self.render_form()
      
  def get(self):
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
                                      ('/oauth/(.*)/(.*)', OAuthHandler),
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()