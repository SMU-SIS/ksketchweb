"""Notifications Module

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

#Handles Notification creation and retrieval
class Notification(db.Model):
  user_id = db.IntegerProperty(required=True) #ID of the User receiving the Notification
  notification_date = db.DateTimeProperty(auto_now_add=True) #The time that the model was created
  
  notification_type = db.StringProperty() #Type of Notification
  other_user = db.IntegerProperty() #The other User involved in the Notification (if applicable)
  # other_info = db.StringProperty()
  relevant_id = db.IntegerProperty() #Relevant information for the Notification
  message = db.StringProperty() #Notification message

  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
       
  #Adds a particular type of Notification
  @staticmethod
  def add(u_id=-1, type="", o_user = 0, o_info = "", r_id = 0):
    if u_id != -1 and type != "":
      #Notification creation
      o_user_name = User.get_name(o_user)
      verify = False
      if type == "GROUPINVITE": #Group invitation for a User
        u_g = UserGroupMgmt.get_by_id(r_id)
        if u_g:
          relevant =  Group.get_name(u_g.group_id)
          notify = Notification(user_id = u_id,
                                notification_type = type,
                                other_user = o_user,
                                relevant_id = r_id,
                                message =  o_user_name + " has invited you to the group " + relevant + ".")
          notify.put()
          verify = True
      elif type == "GROUPACCEPT": #Informs Group Founder of accepted invite
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = r_id,
                              message = o_user_name + " has accepted your invitation to the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPREJECT": #Informs Group Founder of rejected invite
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = r_id,
                              message = o_user_name + " has rejected your invitation to the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPLEAVE": #Informs Group Founder of a member who has left the Group
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = r_id,
                              message = o_user_name + " has left the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPJOINCFM": #Confirms to a User they have joined a Group
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = 0,
                              relevant_id = r_id,
                              message = "You have joined the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPPASSFOUNDER": #Informs User they are now the Founder of a Group
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = r_id,
                              message = o_user_name + " has made you the Founder of the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPEXPEL": #Informs User they have been expelled from a Group
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = r_id,
                              message = o_user_name + " has kicked you from the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPDELETE": #Informs all Users in a Group of its deletion
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = 0,
                              message = o_user_name + " has deleted the group " + o_info + ".")
        notify.put()
        verify = True
      elif type == "GROUPDELCANCEL": #Informs a User pending an invite that said Group was deleted
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = 0,
                              message = o_user_name + " has cancelled your invite and deleted the group " + o_info + ".")
        notify.put()
        verify = True               
      elif type == "ADMINDELETE": #Informs a User that an administrator has deleted their sketch
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = 0,
                              relevant_id = 0,
                              message = "An administrator has deleted your sketch '" + o_info + "'.")
        notify.put()
        verify = True
      return verify
       
  #Gets Notifications for a User, bounded by limits.
  @staticmethod
  def get_entities(user_id=-1, limit=0):
    #update ModelCount when adding
    u_id = int(user_id)
    theQuery = Notification.all()
    theQuery.order('-notification_date')

    objects = theQuery.run()
    utc = UTC()
    entities = []
    count = 0
    for object in objects:
      if object.user_id == int(user_id):
        n_date = object.notification_date.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S")
        o_user = User.get_name(object.other_user)
        
        entity = {'n_date':n_date,
                'id': object.key().id(),
                'n_message': object.message,
                'n_type': object.notification_type,
                'n_relevant': object.relevant_id,
                'user_id': object.user_id}
        entities.append(entity)            
        count += 1
        #Cutoff if limit was defined
        if limit != 0:
          if count == int(limit):
            break
          
    result = {'method':'get_entities',
              'en_type': 'Notification',
              'entities': entities,
              'retrieved': count}      
    return result
    
#Imports placed below to avoid circular imports
from rpx import User, UTC
from sketches import Sketch
from permissions_groups import Group, UserGroupMgmt
from notifications import Notification    
      