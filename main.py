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
    template_values = {
      'pagetitle': 'Welcome to Moustache Wars',
    }
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

HEADER = """
<html><head><title>Twitter OAuth Demo</title>
</head><body>
<h1>Twitter OAuth Demo App</h1>
"""

FOOTER = "</body></html>"

class Login(webapp.RequestHandler):
    def get(self):
        client = OAuthClient('twitter', self)
        #gdata = OAuthClient('google', self, scope='http://www.google.com/calendar/feeds')

        write = self.response.out.write; write(HEADER)

        if not client.get_cookie():
            write('<a href="/oauth/twitter/login">Login via Twitter</a>')
            write(FOOTER)
            return

        write('<a href="/oauth/twitter/logout">Logout from Twitter</a><br /><br />')

        info = client.get('/account/verify_credentials')

        write("<strong>Screen Name:</strong> %s<br />" % info['screen_name'])
        write("<strong>Location:</strong> %s<br />" % info['location'])

        rate_info = client.get('/account/rate_limit_status')

        write("<strong>API Rate Limit Status:</strong> %r" % rate_info)

        write(FOOTER)


application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/upload', Upload),
                                      ('/img', Image),
                                      # Logins
                                      ('/oauth/(.*)/(.*)', OAuthHandler),
                                      ("/login", Login),],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()