
"""Comments & Likes Module

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


    
#Handles Comment data, and creation of comments
class Comment(db.Model):
  sketch_id = db.IntegerProperty() #SketchID of the Sketch Comment is linked to
  user_id = db.IntegerProperty(required=True) #UserID of the User who made the Comment
  content = db.StringProperty(required=True) #Content of the Comment
  reply_to_id = db.IntegerProperty()
  created = db.DateTimeProperty(auto_now_add=True) #The time that the model was created
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d  
  
  #Adds a new Comment entity
  @staticmethod
  def add(data, user_id=-1):
    result = {}
    #try:
    jsonData = json.loads(data)
    
    #For sketch files saved through "Save As"
    if jsonData['sketchId'] != '' and user_id != -1:
      #Check Permissions
      permissions = Permissions.user_access_control(long(jsonData['sketchId']), long(user_id))
        
      if bool(permissions['p_comment']):
        #Placeholder for reply
      
        contentData = jsonData['content']
        contentData = contentData[:255]
          
        entity = Comment(sketch_id=long(jsonData['sketchId']),
                        user_id=long(user_id),
                        content=contentData,
                        reply_to_id=long(jsonData['replyToId']))
          
        verify = entity.put()
        
        result = {'status':"success",
                  'method':"add",
                  'en_type':"Comment"}
      else:
        result = {'status': "error",
                'message': "Sorry, but you are not authorized to comment."}
        
    else:
      result = {'status': "error",
                'message': "Error in posting comment. Please try again."}
    #except:
    #  result = {'status': "error",
    #            'message': "Error in posting comment. Please try again."}
    
    return result       
  
  #Handler wrapper method to call get_entities_by_id via JSON POST
  @staticmethod
  def get_entities_by_id_handler_wrapper(data):
    jsonData = json.loads(data)
    model_id = long(jsonData['id'])
    result = Comment.get_entities_by_id(model_id)
    
    return result
  
  #Gets Comment entities for a specific Sketch
  @staticmethod
  def get_entities_by_id(model_id):
    utc = UTC()
    theQuery = Comment.all()
    #if model:
      #theQuery = theQuery.filter('model', model)

    objects = theQuery.run()

    entities = []
    for object in objects:
      if long(model_id) == object.sketch_id:
        data = {'sketchId': object.sketch_id,
                'user_id': object.user_id,
                'user_name': User.get_name(long(object.user_id)),
                'g_hash': User.get_image(long(object.user_id)),
                'content': object.content,
                'reply_to_id': object.reply_to_id}
          
        entity = {'id': object.key().id(),
              'created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"), 
              'data': data}
              
        entities.append(entity)
       
    result = {'method':'get_entities_by_id',
              'en_type': 'Comment',
              'count': len(entities),
              'entities': entities}
    return result
  
  #Clears comments for a specific Sketch
  @staticmethod  
  def delete_by_sketch(sketch_id):
    theQuery = Comment.all()
    theQuery = theQuery.filter('sketch_id =', long(sketch_id))
    objects = theQuery.run()
    count = 0
    for object in objects:
      object.delete()
      count += 1
    result = {'method':'delete_by_sketch',
              'en_type': 'Comment',
              'sketchId': sketch_id,
              'count': count}
    return result
    
#Handles Like data, and liking/unliking of Sketches
class Like(db.Model):
  sketch_id = db.IntegerProperty() #SketchID of the Sketch Like is linked to
  user_id = db.IntegerProperty(required=True) #UserID of the User who made the Like
  created = db.DateTimeProperty(auto_now_add=True) #The time that the model was 
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
       
  @staticmethod     
  def like_unlike(data, userid):
    result = {}
    try:
      jsonData = json.loads(data)
      sketchId = long(jsonData['sketchId'])
      permissions = Permissions.user_access_control(sketchId, userid)
      
      if bool(permissions['p_view']):
        #Users can only (un)like sketches they can view
        theQuery = Like.all()
        theQuery.filter('sketch_id =', sketchId).filter('user_id =', userid)
        theobject = theQuery.get()
        data = {'sketchId': sketchId,
                'userid': userid,
                'action': ""}
        
        if theobject is None:
          #No existing Like by this user for this sketch - new Like
          newobject = Like(sketch_id = sketchId,
                           user_id = long(userid))
                           
          newobject.put()
          data['action'] = "Like"
        else:
          #Like by this user for this sketch exists - delete Like
          theobject.delete()
          data['action'] = "Dislike"
          
        result = {'status': "success",
                  'method':"add",
                  'en_type':"Like",
                  'data': data}
      else:
        result = {'status': "error",
                  'message': "You are not allowed to view this sketch."}
    except:
      result = {'status': "error",
                'message': "There was an error in updating your like.",
                'submessage': "Please try again later."}
    return result

  @staticmethod
  def check_if_user_likes(sketchId = -1, userid = -1):
    try:
      theQuery = Like.all()
      theQuery.filter('sketch_id =', long(sketchId)).filter('user_id =', long(userid))
      theobject = theQuery.get()
      if theobject:
        return True
      else:
        return False
    except:
      return False
      
  #Handler wrapper method to call get_entities_by_id via JSON POST
  @staticmethod
  def get_entities_by_id_handler_wrapper(data, userid):
    jsonData = json.loads(data)
    model_id = long(jsonData['id'])
    result = Like.get_entities_by_id(model_id, userid)
    
    return result    
      
  @staticmethod
  def get_entities_by_id(sketchId, userid = 0):
    utc = UTC()
    theQuery = Like.all()
    objects = theQuery.run()
    
    entities = []
    for object in objects:
      if object.sketch_id == long(sketchId):
        data = {'id': object.key().id(),
                'sketch_id': object.sketch_id,
                'user_id': object.user_id,
                'user_name': User.get_name(object.user_id),
                'created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S")}
        entities.append(data)
      
    result = {'method':'get_entities_by_id',
              'en_type': 'Like',
              'is_user_like': Like.check_if_user_likes(sketchId, userid),
              'count': len(entities),
              'count_other_users': (len(entities) - 1),
              'entities': entities}
    return result
        
  @staticmethod  
  def delete_by_sketch(sketch_id):
    theQuery = Like.all()
    theQuery = theQuery.filter('sketch_id =', long(sketch_id))
    objects = theQuery.run()
    count = 0
    for object in objects:
      object.delete()
      count += 1
    result = {'method':'delete_by_sketch',
              'en_type': 'Like',
              'sketchId': sketch_id,
              'count': count}
    return result
        
#Imports placed below to avoid circular imports
from rpx import User, UTC
from permissions_groups import Permissions, Sketch_Groups
from notifications import Notification        