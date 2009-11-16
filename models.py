# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Model classes and utility functions for handling
Moustaches, Votes and Voters in the mowars application.

"""


import datetime
import hashlib

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users
import random

PAGE_SIZE = 20
DAY_SCALE = 4

def get_random_taches():
  taches = Moustache.all()
  """Get two random taches from the datastore. This will break with more
    than 1000 taches
  """
  num_taches = total_taches()
  int1 = random.randint(0,num_taches-1)
  int2 = random.randint(0,num_taches-1)
  while int2 == int1:
    int2 = random.randint(0,num_taches-1)
  return taches[int1], taches[int2]

def get_top_taches():
    query = Moustache.all().order('-win_percentage')
    return query.fetch(10)
    
def get_bottom_taches():
    query = Moustache.all().order('win_percentage')
    return query.fetch(10)

def get_taches_by_username(username):
    query  = Moustache.all().filter('name = ', username)
    return query.fetch(20)
    
def get_taches_by_twitpic(twitpic):
    query  = Moustache.all().filter('twitpic = ', twitpic)
    return query.fetch(20)

def total_taches():
  """Find the total number of taches in the datastore
  this will break with more than 1000 taches
  """
  taches = Moustache.all(keys_only=True).count()
  return taches

#!!If we clear the data store these must be reset!!
#default_since = datetime.date(2009,11,01)
#default_until = datetime.date(2009,11,06)
default_since = datetime.date(2009,11,15)
default_until = datetime.date(2009,11,16)

class Spider(db.Model):
    last_search = db.DateTimeProperty(auto_now=True)
    last_since = db.DateProperty(default=default_since)
    last_until = db.DateProperty(default=default_until)
    twitpics = db.StringListProperty()
    last_since_id = db.StringProperty()

def get_spider():
    query = Spider.all().order('-last_search')
    results = query.fetch(1)
    if results:
        return results[0]
    else:
        return False

class Moustache(db.Model):
  """Storage for a single moustache and its metadata
  
  Properties
    name:           The name as a string
    image:          The image as a blob
    uri:            An optional URI that is the source of the quotation
    rank:           A calculated ranking based on the number of votes and when the quote was added.
    created:        Date and time moustache was created
    creator:        The user that added this quote.
  """
  #This is the twitter name! not facebook if we implement that
  name = db.StringProperty()
  modified = db.DateTimeProperty(auto_now=True)
  image = db.BlobProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  wins = db.IntegerProperty(default=0)
  losses = db.IntegerProperty(default=0)
  win_percentage = db.IntegerProperty(default=0)
  #This is the twitter message
  tweet = db.StringProperty(default='', multiline=True)
  #This is the twitpic url
  twitpic = db.StringProperty(default='')
  
  def total_battles(self):
      return self.wins+self.losses
  
  def calc_win_percentage(self):
    total = self.wins+self.losses
    return int((float(self.wins)/total)*100)
      


class Vote(db.Model):
  """Storage for a single vote by a single user on a single quote.
  
  Index
    key_name: The email address of the user that voted.
    parent:   The quote this is a vote for.
  
  Properties
    vote: The value of 1 for like, -1 for dislike.
  """
  created = db.DateTimeProperty(auto_now_add=True)
  winner = db.ReferenceProperty(Moustache,
          collection_name="vote_winner_set")
  loser = db.ReferenceProperty(Moustache,
          collection_name="vote_loser_set")
  name = db.StringProperty(default='Guest')
  ip = db.StringProperty(default='')