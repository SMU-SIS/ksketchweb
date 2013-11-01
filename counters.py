
"""Counters Module

@created: Goh Kian Wei (Brandon), Kevin Koh, Shannon Lim, Tony Tran, Samantha Wee, Wong Si Hui
@code_adapted_from: Chris Boesch, Daniel Tsou
"""
"""
Note to self: json.loads = json string to objects. json.dumps is object to json string.
"""
import datetime
import os
import urllib
import urllib2

import webapp2
from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import json


#Counter increment for Sketch ID and Sketch Count.
#Allows for easier handling of unique Sketch IDs
class ModelCount(db.Model):
  en_type = db.StringProperty(required=True,default='Default-entype') #Type of counter (SketchID, Sketch Count)
  count = db.IntegerProperty(required=True, default=0) #Current counter
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
  
  #Gets counter
  @staticmethod
  def get_counter(en_type):
    return ModelCount.all().filter('en_type',en_type).get()
  
  #Increments counter
  @staticmethod
  def increment_counter(en_type):
    modelCount = ModelCount.all().filter('en_type',en_type).get()
    if modelCount:
      modelCount.count += 1
      modelCount.put()
    else:
      modelCount = ModelCount(en_type='Sketch', count=1)
      modelCount.put()
      
  #Decrements counter
  @staticmethod
  def decrement_counter(en_type):
    modelCount = ModelCount.all().filter('en_type',en_type).get()
    if modelCount:
      modelCount.count -= 1
      modelCount.put()

#Counter increment for version numbers for each Sketch ID.
class VersionCount(db.Model):
  sketchId = db.IntegerProperty(required=True, default=0) #SketchID
  lastVersion = db.IntegerProperty(required=True, default=0) #Latest version of Sketch
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
  
  #Gets counter
  @staticmethod
  def get_counter(sketchId = -1):
    return VersionCount.all().filter('sketchId', long(sketchId)).get()
  
  #Increments counter before retrieving it
  @staticmethod
  def get_and_increment_counter(sketchId = -1):
    versionCount = VersionCount.all().filter('sketchId', long(sketchId)).get()
    if versionCount:
      versionCount.lastVersion += 1
      versionCount.put()
    else:
      versionCount = VersionCount(sketchId=long(sketchId), lastVersion=1)
      versionCount.put()
    return versionCount.lastVersion
  
#Counter increment for number of sketches for each application version.
class AppVersionCount(db.Model):
  app_version = db.FloatProperty() #Version of application
  sketch_count = db.IntegerProperty() #No. of Sketch entities for version
  original_count = db.IntegerProperty() #No. of original Sketches for version
  

  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
  
  #Increments sketch counter (and original, if applicable)
  @staticmethod  
  def increment_counter(app_version = -1, original = True):
    appVersionCount = AppVersionCount.all().filter('app_version', float(app_version)).get()
    if appVersionCount:
      appVersionCount.sketch_count += 1
      if original:
        appVersionCount.original_count += 1
      appVersionCount.put()
    else:
      if original:
        appVersionCount = AppVersionCount(app_version=float(app_version), sketch_count = 1, original_count = 1)
      else:
        appVersionCount = AppVersionCount(app_version=float(app_version), sketch_count = 1, original_count = 0)
      appVersionCount.put()
      
  #Decrements sketch counter (and original, if applicable)
  @staticmethod  
  def decrement_counter(app_version = -1, original = True):
    appVersionCount = AppVersionCount.all().filter('app_version', float(app_version)).get()
    if appVersionCount:
      appVersionCount.sketch_count -= 1
      if original:
        appVersionCount.original_count -= 1
      appVersionCount.put()
  
  #Retrieves counter for a particular version
  @staticmethod
  def retrieve_by_version():
    utc = UTC()
    appver_query = AppVersionCount.all()

    objects = appver_query.run()
    entities = []
    total_user_count = 0
    total_sketch_count = 0
    total_original_count = 0
    for object in objects:

      entity = {'app_version': object.app_version,
            'user_count': 0,
            'sketch_count': object.sketch_count,
            'original_count': object.original_count}
            
      appuser_query = AppUserCount.get_counter(float(object.app_version))
      if appuser_query:
        entity['user_count'] = int(appuser_query.user_count)
      total_user_count += appuser_query.user_count
      total_sketch_count += object.sketch_count
      total_original_count += object.original_count
      entities.append(entity)    
    
    total = {'app_version': 'Total',
            'user_count': total_user_count,
            'sketch_count': total_sketch_count,
            'original_count': total_original_count}
    
            
    
    result = {'method':'retrieve_by_version',
              'en_type': 'AppVersionCount',
              'status':'success',
              'entities': entities,
              'total': total}  
    return result
        
#Counter increment for Users for a particular App version
class AppUserCount(db.Model):
  app_version = db.FloatProperty()
  user_count = db.IntegerProperty()
  

  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d  
          #Gets counter
  @staticmethod
  def get_counter(appver = 1.0):
    return AppUserCount.all().filter('app_version', appver).get()
  
  #Increments counter before retrieving it
  @staticmethod
  def get_and_increment_counter(appver = 1.0):
    appUserCount = AppUserCount.all().filter('app_version', appver).get()
    if appUserCount:
      appUserCount.user_count += 1
      appUserCount.put()
    else:
      appUserCount = AppUserCount(app_version=appver,user_count = 1)
      appUserCount.put()
    return appUserCount
    
#Imports placed below to avoid circular imports
from rpx import UTC