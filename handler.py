'''
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
'''
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
import logging

from webapp2_extras import auth
from webapp2_extras import sessions
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

import webapp2
from google.appengine.api import memcache
from google.appengine.ext import db, webapp,deferred
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

    #Handler for adding a Sketch when there is a discrepancy
    def add_sketch_discrepancy(self): #/add/sketch
      auser = self.auth.get_user_by_session()
      userid = 0
      if auser:
        userid = auser['user_id']
      
      result = Sketch.addDiscrepancy(self.request.body, userid=userid)
      return self.respond(result)

    #Handler for adding a Sketch
    def add_sketch(self): #/add/sketch
    
        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
          
        result = Sketch.add(self.request.body, userid=userid)
        return self.respond(result)
    
    def overwrite_get(self):
        flexData = self.request.get("fileData")
        userid = self.request.get("userid")

        result = Sketch.addDiscrepancy(flexData, userid=userid)
        return self.respond(result)

    def post(self):
        flexData = self.request.get("fileData")
        userid = self.request.get("userid")

        result = Sketch.add(flexData, userid=userid)
        return self.respond(result)

    def delete_sketch_mobile(self):
        sketchid = self.request.get("sketchid")
        userid = self.request.get("userid")

        result = Sketch.delete_mobile(sketchid, userid=userid)
        return self.respond(result)

    def delete_sketch_permenently(self):
        sketchid = self.request.get("sketchid")
        userid = self.request.get("userid")

        result = Sketch.delete_sketch_permenently(sketchid, userid=userid)
        return self.respond(result)

    def restore_sketch(self):
        sketchid = self.request.get("sketchid")
        userid = self.request.get("userid")

        result = Sketch.restore_sketch(sketchid, userid=userid)
        return self.respond(result)

    #Handler for deleting a Sketch - NOT WORKING
    def delete_sketch(self, model_id):  #/delete/sketch/<model_id>

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
        result = Sketch.remove(model_id, userid)
        
        return self.respond(result)
    
    #Handler for listing Sketches by User   
    def user_sketch(self): #/list/sketch/user 
        
        userid = 0

        jsonData = json.loads(self.request.body)
        parentalview = jsonData['urltype']
        if parentalview == "parent":
          userid = jsonData['id']

        auser = self.auth.get_user_by_session()
        
        if auser:
          userid = auser['user_id']
        
        result = Sketch.get_entities_by_id(self.request.body, userid=userid)
        return self.respond(result)    


    def view_trash_sketches(self): #/get/trash/user

        userid = 0

        jsonData = json.loads(self.request.body)
        parentalview = jsonData['urltype']
        if parentalview == "parent":
          userid = jsonData['id']

        auser = self.auth.get_user_by_session()

        if auser:
          userid = auser['user_id']

        result = Trash.get_entities_by_id(self.request.body, userid=userid)
        return self.respond(result)


    #Test method by Cam
    def user_sketch_mobile(self, criteria): #/list/sketch/user
        result = Sketch.get_entities_by_criteria(criteria=criteria)
        return self.respond(result)

    def user_latest_sketch(self,json="{}"): #/list/sketch/latest
        auser = self.auth.get_user_by_session()
        result = {'status':'error',
              'message':'There was an error getting the list.',
              'submessage':'Please try again later.'}
        if self.request.method=="GET":
          result = Sketch.get_latest_by_criteria(json)
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

        userid = 0
        
        jsonData = json.loads(self.request.body)
        parentalview = jsonData['urltype']
        if parentalview == "parent":
          userid = jsonData['urlid']

        auser = self.auth.get_user_by_session()
        
        if auser:
          userid = auser['user_id']
        
        result = Sketch.get_entity_by_versioning(self.request.body, "View", userid=userid)
        
        logging.info(result)
        return self.respond(result)   

    #Handler for viewing a particular Sketch mobile
    def view_sketch_mobile(self, sketchId, version, userid): #/get/sketch/view/<sketchId>/<version>/<userid>
        result = Sketch.get_entity_by_versioning_mobile(sketchId, version, "View", userid=userid)
        return self.respond(result)   

    #Handler for editing a particular Sketch      
    def edit_sketch(self): #/get/sketch/edit

        userid = 0
        
        jsonData = json.loads(self.request.body)
        parentalview = jsonData['urltype']
        if parentalview == "parent":
          userid = jsonData['urlid']

        auser = self.auth.get_user_by_session()
        
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

    #Test method by Ram. Which loads sketches without thumbnails
    def user_sketch_lite(self, criteria): #/list/sketch/user
        result = Sketch.get_entities_lite(criteria=criteria)
        return self.respond(result)
    #Test method by Ram.
    def get_filenames(self, criteria): #/list/sketch/user
        result = Sketch.get_filenames(criteria=criteria)
        return self.respond(result)
    def get_thumbnail(self, criteria): #/list/sketch/user
        result = Sketch.get_thumbnail(criteria=criteria)
        return self.respond_thumbnail(result)
    #Response wrapper for handler
    def respond_thumbnail(self,result):
        """Returns a JSON response to the client.
        """
        callback = self.request.get('callback')
        self.response.headers['Content-Type'] = 'image/png'
        #self.response.headers['Content-Type'] = '%s; charset=%s' % (config.CONTENT_TYPE, config.CHARSET)
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD'
        self.response.headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, X-Requested-With'
        self.response.headers['Access-Control-Allow-Credentials'] = 'True'
        self.response.headers['Access-Control-Allow-Credentials'] = 'True'
        self.response.headers['Content-Transfer-Encoding'] = 'base64'
        #Add a handler to automatically convert datetimes to ISO 8601 strings.
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        return self.response.out.write(result)
    def user_sketch_mobile_v2(self, criteria): #/list/sketch/user
        result = Sketch.get_entities_v2(criteria=criteria)
        return self.respond(result)
    def update_handle(self):
        deferred.defer(sketches.UpdateSchema)
        self.response.out.write('Schema migration successfully initiated.')
    def update_file(self):
        deferred.defer(sketches.UpdateLowerFilenames)
        self.response.out.write('Schema migration successfully initiated.')


    def modify_fileData(self): #/add/sketch
      result = Sketch.modify_sketch_data(self.request.body)
      return self.respond(result)

    def send_svg(self,sketchId, version, userid): # /get/svg/view/<sketchId>
        cache = SVGCache.getSVGCache(sketchId, version)
        if cache and cache.svgData:
            return self.respond({"data":'<svg id="mySVG" viewport-fill="white" xmlns="http://www.w3.org/2000/svg"  version="1.1" width="100%" style="overflow: hidden; left: 0px; top: 0px;stroke-width: 0px; background-color: white;" viewBox="0 0 1280 710" preserveAspectRatio="xMaxYMax meet">' +cache.svgData + '</svg>'})
        else:
            result = Sketch.get_file_data(sketchId, version, "View", userid=userid)
            result = ksketchsvg.get_svg(result.decode("string-escape"),sketchId,version)
        return self.respond({"data":'<svg id="mySVG" viewport-fill="white" xmlns="http://www.w3.org/2000/svg" ng-click="pauseOrPlay($event)" version="1.1" width="100%" style="overflow: hidden; left: 0px; top: 0px;stroke-width: 0px; background-color: white;" viewBox="0 0 1280 710" preserveAspectRatio="xMaxYMax meet">' +result + '</svg>'})

    def send_script(self,sketchId, version, userid): # /get/svg/view/<sketchId>
        cache = SVGCache.getSVGCache(sketchId, version)
        if cache and cache.animationData:
            return self.respond(json.loads(cache.animationData))
        else:
            result = Sketch.get_file_data(sketchId, version, "View", userid=userid)
            result = ksketchsvg.get_transformations(result.decode("string-escape"),sketchId,version)
            return self.respond(result)
    #Handler for viewing a particular Sketch mobile
    def view_sketch_xml(self, sketchId, version, userid): #/get/sketch/view/<sketchId>/<version>/<userid>
        result = Sketch.get_xml_by_versioning_mobile(sketchId, version, "View", userid=userid)
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
    webapp2.Route('/add/sketchDiscrepancy', handler=ActionHandler, handler_method='add_sketch_discrepancy'), # Add Sketch with discrepancy
    webapp2.Route('/list/sketch', handler=ActionHandler, handler_method='list_sketch'), # List/Search Sketch
    webapp2.Route('/list/sketch/user', handler=ActionHandler, handler_method='user_sketch'), # List Sketch By User
    webapp2.Route('/list/sketch/user/<criteria>', handler=ActionHandler, handler_method='user_sketch_mobile'), # List Sketch By User
    webapp2.Route('/list/sketch/latest/<json>', handler=ActionHandler, handler_method='user_latest_sketch'),
    webapp2.Route('/list/sketch/group', handler=ActionHandler, handler_method='group_sketch'), # List Sketch By Group
    webapp2.Route('/get/sketch/view', handler=ActionHandler, handler_method='view_sketch'), # Get Sketch (View)
    webapp2.Route('/get/sketch/view/<sketchId>/<version>/<userid>', handler=ActionHandler, handler_method='view_sketch_mobile'), # Get Sketch (View)
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
    
    webapp2.Route('/list/version', handler=ActionHandler, handler_method='get_versions'), # Get Versions
    webapp2.Route('/get/overwritesketchxml', handler=ActionHandler, handler_method='overwrite_get'),
    webapp2.Route('/get/deletesketch', handler=ActionHandler, handler_method='delete_sketch_mobile'),
    webapp2.Route('/get/deletepermenently', handler=ActionHandler, handler_method='delete_sketch_permenently'),
     webapp2.Route('/get/restoresketch', handler=ActionHandler, handler_method='restore_sketch'),
    webapp2.Route('/get/sketchxml', handler=ActionHandler),
    webapp2.Route('/list/sketch/user_lite/<criteria>', handler=ActionHandler, handler_method='user_sketch_lite'), # List Sketch By User
    webapp2.Route('/get/thumbnail/<criteria>', handler=ActionHandler, handler_method='get_thumbnail'),
    webapp2.Route('/get/filenames/<criteria>', handler=ActionHandler, handler_method='get_filenames'),
    webapp2.Route('/list/sketch_v2/user/<criteria>', handler=ActionHandler, handler_method='user_sketch_mobile_v2'),
    webapp2.Route('/updateHandler', handler=ActionHandler, handler_method='update_handle'),
    webapp2.Route('/updateFileNames', handler=ActionHandler, handler_method='update_file'),
    webapp2.Route('/modify/fileData', handler=ActionHandler, handler_method='modify_fileData'),
    webapp2.Route('/get/svg/view/<sketchId>/<version>/<userid>', handler=ActionHandler, handler_method='send_svg'),
    webapp2.Route('/get/svg/script/<sketchId>/<version>/<userid>', handler=ActionHandler, handler_method='send_script'),
    webapp2.Route('/get/sketch/view_xml/<sketchId>/<version>/<userid>', handler=ActionHandler, handler_method='view_sketch_xml'),
    webapp2.Route('/get/trash/user',handler=ActionHandler, handler_method='view_trash_sketches')], # Get Sketch (View)],
    config=webapp2_config,
    debug=True)
    

#Imports placed below to avoid circular imports
from rpx import User
import sketches
from sketches import Sketch
from counters import AppVersionCount
from comments_likes import Comment, Like
from permissions_groups import Sketch_Groups, Group, UserGroupMgmt
from notifications import Notification
from ksketchsvg import ksketchsvg
from svgcache import SVGCache
from trash import Trash