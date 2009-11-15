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
  

def total_taches():
  """Find the total number of taches in the datastore
  this will break with more than 1000 taches
  """
  taches = Moustache.all(keys_only=True).count()
  return taches


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
  name = db.StringProperty(multiline=True)
  modified = db.DateTimeProperty(auto_now=True)
  image = db.BlobProperty()
  uri   = db.StringProperty()
  rank = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  votesum = db.IntegerProperty(default=0)
  creator = db.UserProperty()
  wins = db.IntegerProperty(default=0)
  losses = db.IntegerProperty(default=0)


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