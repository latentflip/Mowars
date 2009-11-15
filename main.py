import cgi, os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from models import Moustache


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
      tache.image = self.request.get('image')
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

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/upload', Upload)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()