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

from models import Moustache, get_random_taches, Vote, get_top_taches, get_bottom_taches, get_spider, Spider, get_taches_by_username, get_taches_by_twitpic, check_vote_spam

class BasicPage(webapp.RequestHandler):
    template_file = ''
    
    def render_template(self, template_values, template_file=''):
        if not template_file:
            template_file = self.template_file
        path = os.path.join(os.path.dirname(__file__), 'templates/'+template_file)
        self.response.out.write(template.render(path, template_values))

class MainPage(BasicPage):
    template_file = 'index.html'
    def get(self):
        extra_values = {}
        try:
            loser = Moustache.get_by_id(int(self.request.get('l')))
            winner = Moustache.get_by_id(int(self.request.get('w')))
            extra_values['last_winner'] = winner
            extra_values['last_loser'] = loser
        except:
            pass

        template_values = self.auth_and_taches()
        template_values.update(extra_values)
        
        self.render_template(template_values)
        
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
        
        #To store username if the user is logged in
        client = OAuthClient("twitter", self)
        logged_in = client.get_cookie()
        
        if logged_in:
            info = client.get("/account/verify_credentials")
            vote.name = info["screen_name"]
        else:
            vote.name = 'Guest'
        
        #TODO: Stop spam-voting for same key from same ip repeatedly
        vote.ip = self.request.remote_addr
        
        if check_vote_spam(vote.ip, winner):
            self.redirect('/msg=You+appear+to+be+votespamming,+please+stop+or+try+again+later')
        else:
            vote.put()
        
            #Wins and losses
            loser.losses = loser.losses+1
            loser.win_percentage = loser.calc_win_percentage()
            loser.put()
        
            winner.wins = winner.wins+1
            winner.win_percentage = winner.calc_win_percentage()
            winner.put()
        
            #Redirect so that people cannot repost twice
            self.redirect('/?w=%s&l=%s' % (winner.key().id(), loser.key().id()))

class CountVote(BasicPage):
    def get(self):
        win_key = str(self.request.get('k'))
        winner = db.get(win_key)
        ip = str(self.request.remote_addr)
        count = check_vote_spam(ip, winner)
        self.response.out.write(str(win_key)+' '+str(count)+' '+ip)

class Top10(BasicPage):
    template_file = 'topbottom.html'
    def get(self):
        """Returns the top 10 taches template"""
        taches = get_top_taches()
        template_values = {
            'page-title': 'Top 10 Taches',
            'taches': taches,
            'ranking_type': 'Top',
        }
        self.render_template(template_values)
  
class Bottom10(BasicPage):
    template_file = 'topbottom.html'
    def get(self):
        """Returns the bottom 10 taches template"""
        taches = get_bottom_taches()
        template_values = {
            'pagetitle': 'Bottom 10 Taches',
            'taches': taches,
            'ranking_type': 'Bottom',
        }
        self.render_template(template_values)

class Profile(BasicPage):
    template_file = 'profile.html'
    def get(self, username):
        taches = get_taches_by_username(username)
        template_values = {
            'page-title': 'Profile For '+username,
            'twitter_username': username,
            'taches': taches,
            'ranking_type': 'Top',
        }
        self.render_template(template_values)

class GetByTwitpic(BasicPage):
    template_file = 'profile.html'
    def get(self, twitpic):
        taches = get_taches_by_twitpic(twitpic)
        template_values = {
            'page-title': 'Twitpics For '+twitpic,
            'taches': taches,
            'ranking_type': 'Top',
        }
        self.render_template(template_values)

class GrabTwitter(webapp.RequestHandler):
    def get(self):
        today = date.today()
        
        #Get the spider, or create it if we lost it
        spider = get_spider()
        if not spider:
            spider = Spider()
            spider.put()
        
        #Find the list of pictures the spider has already found
        twitpic_spider_list = spider.twitpics
        
        #Api to call twitter
        twitter_search = twapi.Twitter(domain="search.twitter.com")
        twitter_search.encoded_args = 'q=&ands=&phrase=twitpic&ors=%23movember+%23mowars&since=' + str(spider.last_since) + '&rpp=100&until=' + str(spider.last_until)
        tw_search_results = twitter_search.search()
        
        #Find twitpic links
        reg = re.compile(r'http://(www)?twitpic.com/([^\s]*)\s*', re.I)
        
        results = []
        for twt in tw_search_results['results']:
            #Crudely try to find original tweeter
            message = twt['text']
            if 'RT' not in message[0:8]:
                #Find all twitpics
                res = reg.findall(twt['text'])
                for url_groups in res:
                    #This is just the twitpic link slug
                    twitpic_url = url_groups[1]
                    #Make a tache
                    tache = Moustache(name=twt['from_user'], tweet=twt['text'], twitpic = twitpic_url)
                    
                    #Don't regrab if an older one has 
                    if twitpic_url not in twitpic_spider_list:
                        try:
                            tache_image = images.resize(get_twitpic_image(twitpic_url), 350, 350)
                            tache.image = db.Blob(tache_image)
                            tache.put()
                            twitpic_spider_list.append(twitpic_url)
                            results.append(dict)
                        except:
                            pass
        
        #Increase limits by a day a time, or just keep it as today and yesterday
        one_day = timedelta(days=1)
        spider.last_since = spider.last_until
        new_until = spider.last_until + one_day
        if new_until<=today:
            spider.last_until = new_until
        else:
            spider.last_until = today
            spider.last_since = today - one_day
        spider.twitpics = twitpic_spider_list
        spider.put()
        self.response.out.write(spider.last_until)
        self.response.out.write(spider.last_since)
        self.response.out.write('\n\n<br><br>')
        self.response.out.write(results)
        self.response.out.write('\n\n<br><br>')
        self.response.out.write(tw_search_results)

class Upload(BasicPage):
    def post(self):
        client = OAuthClient("twitter", self)
        logged_in = client.get_cookie()
        if not logged_in:
            self.redirect("/")
          
        twitter_info = client.get("/account/verify_credentials")
        tache = Moustache()
        
        if self.request.get('add-tache'):
            tache.name = twitter_info["screen_name"]
            tache_image = images.resize(self.request.get('image'), 350, 350)
            tache.image = db.Blob(tache_image)
            tache.put()
            self.redirect('/profile/'+tache.name)
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
        self.render(template_values)

class Image (webapp.RequestHandler):
    """Returns an image file based on a tache key (not id)"""
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
                                      ('/tashwin', Top10),
                                      ('/tashfail', Bottom10),
                                      ('/grabtwitter', GrabTwitter),
                                      ('/profile/(.*)', Profile),
                                      ('/tp/(.*)', GetByTwitpic),
                                      ('/cnt', CountVote),
                                      # Logins
                                      ('/oauth/(.*)/(.*)', OAuthHandler)
                                     ],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()