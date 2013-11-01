
"""Backend Handler Module

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

from webapp2_extras import auth
from webapp2_extras import sessions
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

import webapp2
from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import json

#Class for all backend URI handlers
class ActionHandler(webapp2.RequestHandler):
    
    #Methods for retrieving authentication
    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)
    
    @webapp2.cached_property
    def session(self):
      # Returns a session using the default cookie key.
      return self.session_store.get_session()
    
    #Response wrapper for handler    
    def respond(self,result):
        """Returns a JSON response to the client.
        """
        callback = self.request.get('callback')
        self.response.headers['Content-Type'] = 'application/json'
        #self.response.headers['Content-Type'] = '%s; charset=%s' % (config.CONTENT_TYPE, config.CHARSET)
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
        self.response.headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, X-Requested-With'
        self.response.headers['Access-Control-Allow-Credentials'] = 'True'

        #Add a handler to automatically convert datetimes to ISO 8601 strings. 
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        if callback:
            content = str(callback) + '(' + json.dumps(result,default=dthandler) + ')'
            return self.response.out.write(content)
            
        return self.response.out.write(json.dumps(result,default=dthandler)) 

    #Handler for adding a Sketch
    def add_sketch(self): #/add/sketch
    
        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
          
        result = Sketch.add(self.request.body, userid=userid)
        return self.respond(result)
    
    #Handler for deleting a Sketch
    def delete_sketch(self, model_id):  #/delete/sketch/<model_id>

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
        result = Sketch.remove(model_id, userid)
        
        return self.respond(result)
    
    #Handler for listing Sketches by User   
    def user_sketch(self): #/list/sketch/user

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
          
        result = Sketch.get_entities_by_id(self.request.body,userid=userid)
        return self.respond(result)    
        
    #Handler for listing Sketches by Group          
    def group_sketch(self): #/list/sketch/group

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
          
        result = Sketch.get_entity_by_group(self.request.body,userid=userid)
        return self.respond(result)    
        
    #Handler for searching for Sketches      
    def list_sketch(self): #/list/sketch

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
          
        result = Sketch.get_entities(self.request.body, userid=userid)
        return self.respond(result)

    #Handler for viewing a particular Sketch
    def view_sketch(self): #/get/sketch/view

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
        
        result = Sketch.get_entity_by_versioning(self.request.body, "View", userid=userid)
        return self.respond(result)    

    #Handler for editing a particular Sketch      
    def edit_sketch(self): #/get/sketch/edit

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
        
        result = Sketch.get_entity_by_versioning(self.request.body, "Edit", userid=userid)
        return self.respond(result) 
     
    #Handler for creating a Group     
    def add_group(self): #/add/group
        if self.request.method=="POST":
          result = Group.add(self.request.body)
          return self.respond(result)
    
        else:
          data = self.request.get("obj")
          if data: 
            result = Group.add(data)
          return self.respond(result)

    #Handler for getting a Group         
    def get_group(self): #/get/group

        result = Group.get_entity(self.request.body)
        return self.respond(result) 

    #Handler for getting Groups for a particular User
    def user_group(self): #/list/group

        offset = 0
        new_offset = self.request.get("offset")
        if new_offset:
          offset = int(new_offset)

        result = UserGroupMgmt.get_entities(self.request.body)
        return self.respond(result)

    #Handler for getting Users in a particular Group       
    def check_user_group(self):  #/listuser/group
      result = {'status':'error',
                'message':''}
      entities = UserGroupMgmt.check_users(self.request.body)
      result = {'status':'success',
                'method':'check_user_group',
                'en_type': 'User',
                'entities': entities}
      return self.respond(result)

        
    #Handler for inviting a User to a Group        
    def add_user_group(self):  #/adduser/group
        auser = self.auth.get_user_by_session()
        result = {'status':'error',
              'message':'There was an error in sending the invite.',
              'submessage':'Please try again later.'}    
        if auser:
          userid = auser['user_id']
          result = UserGroupMgmt.add(self.request.body, userid)
        return self.respond(result)
        
    #Handler for removing a User/quitting from a Group                
    def remove_user_group(self):  #/removeuser/group
        auser = self.auth.get_user_by_session() 
        if auser:
          userid = auser['user_id']
          result = UserGroupMgmt.remove_user(self.request.body, userid)
        return self.respond(result)   
        
    #Handler for passing ownership of a Group to another User        
    def pass_founder_group(self):  #/passfounder/group
        auser = self.auth.get_user_by_session() 
        if auser:
          userid = auser['user_id']
          result = UserGroupMgmt.pass_founder(self.request.body, userid)
        return self.respond(result)        
        
    #Handler for accepting/rejecting a Group invite               
    def accept_reject_group(self):  #/acceptreject/group
        auser = self.auth.get_user_by_session()
        result = {'status':'error',
              'message':'Not authenticated.'}
        if auser:
          userid = auser['user_id']
          result = UserGroupMgmt.accept_reject(self.request.body, userid)
        return self.respond(result) 
        
    #Handler for deleting a Group        
    def delete_group(self):  #/delete/group
        auser = self.auth.get_user_by_session()
        result = {'status':'error',
              'message':'Not authenticated.'}
        if auser:
          userid = auser['user_id']
          result = Group.remove(self.request.body, userid)
        return self.respond(result)      
        
    #Handler for getting latest Notifications
    def get_notification(self, limit):  #/get/notification/<limit>
        auser = self.auth.get_user_by_session()
        result = {}
        if auser:
          userid = auser['user_id']
          result = Notification.get_entities(userid, limit)
        return self.respond(result)
        
    #Handler for getting all Notifications
    def get_all_notification(self):  #/get/notification
        auser = self.auth.get_user_by_session()
        result = {}
        if auser:
          userid = auser['user_id']
          result = Notification.get_entities(userid)
        return self.respond(result)        
          
    #Handler for adding a Comment to a Sketch
    def add_comment(self):  #/add/comment
        auser = self.auth.get_user_by_session()
        result = {'status':'error',
              'message':'There was an error in adding the comment.',
              'submessage':'Please try again later.'}    
        if auser:
          userid = auser['user_id']
          if self.request.method=="POST":
            result = Comment.add(self.request.body, userid)
      
          else:
            data = self.request.get("obj")
            if data: 
              result = Comment.add(data, userid)
        return self.respond(result)        
        
    #Handler for getting Comments for a Sketch               
    def get_comment(self):  #/get/comment
        auser = self.auth.get_user_by_session()
        if auser:
          userid = auser['user_id']
        result = Comment.get_entities_by_id_handler_wrapper(self.request.body)
        return self.respond(result) 
          
    #Handler for Liking/Unliking a Sketch                  
    def toggle_like(self):  #/toggle/like
        auser = self.auth.get_user_by_session()
        result = {'status':'error',
              'message':'There was an error in liking/unliking the sketch.',
              'submessage':'Please try again later.'}    
        if auser:
          userid = auser['user_id']
          if self.request.method=="POST":
            result = Like.like_unlike(self.request.body, userid)
      
          else:
            data = self.request.get("obj")
            if data: 
              result = Like.like_unlike(data, userid)
        return self.respond(result)        
        
    #Handler for getting Likes for a sketch                
    def get_like(self):  #/get/like
        
        auser = self.auth.get_user_by_session()
        if auser:
          userid = auser['user_id']
          result = Like.get_entities_by_id_handler_wrapper(self.request.body, userid)
        else:
          result = Like.get_entities_by_id_handler_wrapper(self.request.body, 0)
        return self.respond(result)            
        
    #Handler for getting Sketches/Users by app version
    def get_versions(self):  #/list/version

        offset = 0
        new_offset = self.request.get("offset")
        if new_offset:
          offset = int(new_offset)

        result = AppVersionCount.retrieve_by_version()
        return self.respond(result)
   
#Configuration and URI mapping
webapp2_config = {}
webapp2_config['webapp2_extras.sessions'] = {
		'secret_key': 'n\xd99\xd4\x01Y\xea5/\xd0\x8e\x1ba\\:\x91\x10\x16\xbcTA\xe0\x87lf\xfb\x0e\xd2\xc4\x15\\\xaf\xb0\x91S\x12_\x86\t\xadZ\xae]\x96\xd0\x11\x80Ds\xd5\x86.\xbb\xd5\xcbb\xac\xc3T\xaf\x9a+\xc5',
	}

application = webapp2.WSGIApplication([
    webapp2.Route('/metadata', handler=ActionHandler, handler_method='metadata'),
    webapp2.Route('/delete/sketch/<model_id>', handler=ActionHandler, handler_method='delete_sketch'), 
    webapp2.Route('/add/sketch', handler=ActionHandler, handler_method='add_sketch'), # Add Sketch
    webapp2.Route('/list/sketch', handler=ActionHandler, handler_method='list_sketch'), # List/Search Sketch
    webapp2.Route('/list/sketch/user', handler=ActionHandler, handler_method='user_sketch'), # List Sketch By User
    webapp2.Route('/list/sketch/group', handler=ActionHandler, handler_method='group_sketch'), # List Sketch By Group
    webapp2.Route('/get/sketch/view', handler=ActionHandler, handler_method='view_sketch'), # Get Sketch (View)
    webapp2.Route('/get/sketch/edit', handler=ActionHandler, handler_method='edit_sketch'), # Get Sketch (Edit)
    webapp2.Route('/add/group', handler=ActionHandler, handler_method='add_group'), # Add Group
    webapp2.Route('/get/group', handler=ActionHandler, handler_method='get_group'), # Get Group
    webapp2.Route('/list/group', handler=ActionHandler, handler_method='user_group'), # 
    webapp2.Route('/listuser/group', handler=ActionHandler, handler_method='check_user_group'), #
    webapp2.Route('/adduser/group', handler=ActionHandler, handler_method='add_user_group'), # Invite User To Group
    webapp2.Route('/removeuser/group', handler=ActionHandler, handler_method='remove_user_group'), # Expel User To Group/Leave Group
    webapp2.Route('/passfounder/group', handler=ActionHandler, handler_method='pass_founder_group'), # Pass Group Founder Position
    webapp2.Route('/acceptreject/group', handler=ActionHandler, handler_method='accept_reject_group'), # Accept/Reject Group Invite
    webapp2.Route('/delete/group', handler=ActionHandler, handler_method='delete_group'), # Delete Group
    webapp2.Route('/get/notification/<limit>', handler=ActionHandler, handler_method='get_notification'), # Get Notifications (Menu)
    webapp2.Route('/get/notification', handler=ActionHandler, handler_method='get_all_notification'), # Get All Notifications
    
    webapp2.Route('/add/comment', handler=ActionHandler, handler_method='add_comment'), # Add Comment
    webapp2.Route('/get/comment', handler=ActionHandler, handler_method='get_comment'), # Get Comment For Sketch
    
    webapp2.Route('/toggle/like', handler=ActionHandler, handler_method='toggle_like'), # Add Comment
    webapp2.Route('/get/like', handler=ActionHandler, handler_method='get_like'), # Get Comment For Sketch
    
    webapp2.Route('/list/version', handler=ActionHandler, handler_method='get_versions') # Get Versions
    ],
    config=webapp2_config,
    debug=True)
    

#Imports placed below to avoid circular imports
from rpx import User
from sketches import Sketch
from counters import AppVersionCount
from comments_likes import Comment, Like
from permissions_groups import Sketch_Groups, Group, UserGroupMgmt
from notifications import Notification    