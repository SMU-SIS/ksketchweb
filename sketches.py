"""Backend Module

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


"""
Attributes and functions for Sketch entity
"""

#Handles Sketch data, and saving and loading of sketches
class Sketch(db.Model):
  #Use backend record id as the model id for simplicity
  sketchId = db.IntegerProperty(required=True) #Sketch ID of Sketch. For common identification for multiple versions of the same sketch.
  version = db.IntegerProperty(required=True) #Version of Sketch.
  changeDescription = db.StringProperty() #Description of Sketch
  fileName = db.StringProperty(required=True) #Sketch name
  owner = db.IntegerProperty(required=True) #User who created the Sketch
  fileData = db.TextProperty(required=True) #Content data of Sketch (XML string)
  thumbnailData = db.TextProperty() #Encoded thumbnail data of Sketch
  original_sketch = db.IntegerProperty(required=True) #SketchID of Sketch that this Sketch was created from (if applicable)
  original_version = db.IntegerProperty(required=True) #Version of Sketch that this Sketch was created from (if applicable)
  created = db.DateTimeProperty(auto_now_add=True) #The time that the model was created    
  modified = db.DateTimeProperty(auto_now=True)
  appver = db.FloatProperty()
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d

  #Creates a new Sketch entity 
  @staticmethod
  def add(data, userid):
    result = {}
    #try:
    #update ModelCount when adding
    jsonData = json.loads(data)
    if jsonData['fileName'].strip() != "":
      #Check if sketch is original
      check_original = False
      #Check if sketch is a new version
      check_new_version = False
      #Check if sketch was made from latest version if not original
      check_if_latest = True
      
      ModelCount.increment_counter('Sketch_count')
      modelCount = ModelCount.get_counter('Sketch')
      
      #For new sketches/sketches saved as new sketches
      if jsonData['sketchId'] == "":
        #Assigns new SketchId
        ModelCount.increment_counter('Sketch')
        jsonData['sketchId'] = str(modelCount.count)
      
      #Placeholder for current version of SketchId
      versionCount = 0
      
      #If sketch is completely original (i.e. new sketch)
      if jsonData['originalSketch'] == -1:
        check_original = True
        #Creates new version counter for the new Sketch.
        versionCount = VersionCount.get_and_increment_counter(long(jsonData['sketchId']))
        jsonData['originalVersion'] = versionCount
        jsonData['originalSketch'] = str(modelCount.count)
        
      #If sketch is an updated version of existing sketch (i.e. edit sketch)
      elif jsonData['originalSketch'] == jsonData['sketchId']:
        v_count = VersionCount.get_counter(long(jsonData['sketchId']))
        versionCount = v_count.lastVersion
        check_new_version = True
        #Updated sketch was created from latest version (ALLOWED)
        if long(jsonData['originalVersion']) == versionCount:
          #Incrementing counter
          versionCount = VersionCount.get_and_increment_counter(long(jsonData['sketchId']))
        #Updated sketch was NOT created from latest version (HALT!)
        else:
          check_if_latest = False
      #If sketch is a new sketch created from an existing sketch (i.e. save as sketch)
      else:
        #Creates new version counter for the new Sketch.
        versionCount = VersionCount.get_and_increment_counter(long(jsonData['sketchId']))
        
      
      #If sketch was an updated sketch created from latest version, a sketch saved as a new sketch, or completely original.
      if check_if_latest:
        allow_permissions = False
        if not check_new_version:
          allow_permissions = True
        elif long(userid) == long(jsonData['owner_id']):
          allow_permissions = True
        elif User.check_if_admin(long(userid)):
          allow_permissions = True
          
        
        #update AppVersionCount when adding
        AppVersionCount.increment_counter(float(jsonData['appver']), check_original)
        
        jsonData['version'] = str(versionCount)
        file = jsonData['fileData']
        thumbnail = jsonData['thumbnailData']
        change = jsonData['changeDescription']
        change = change[:255]
          
        entity = Sketch(sketchId=long(jsonData['sketchId']),
                        version=long(jsonData['version']),
                        changeDescription=change,
                        fileName=jsonData['fileName'],
                        owner=long(jsonData['owner_id']),
                        fileData=file,
                        thumbnailData=thumbnail,
                        original_sketch=long(jsonData['originalSketch']),
                        original_version=long(jsonData['originalVersion']),
                        appver=float(jsonData['appver']))
        
        verify = entity.put()
        if (allow_permissions):
          if (verify):
            
            permissions_key = Permissions.add(long(jsonData['sketchId']),
                                              bool(long(jsonData['p_view'])),
                                              bool(jsonData['p_edit']),
                                              bool(jsonData['p_comment']))
            #Update group permissions when adding
            
            group_count = 0
            #try:
            if jsonData['group_permissions']:
              group_permissions = jsonData['group_permissions']
              group_count = Sketch_Groups.add(long(jsonData['sketchId']),
                                              group_permissions)
            #except:
             # group_count = 0
          
            if (permissions_key != -1):
              result = {'id': entity.key().id(), 
                        'status': "success",
                        'method': "add",
                        'en_type': "Sketch",
                        'data': jsonData} #this would also check if the json submitted was valid
            
            else:
              #Rollback
              rollback = Sketch.get_by_id(entity.key.id())
              if rollback:
                rollback.delete()
              result = {'status': "error",
                       'message': "Save unsuccessful. Please try again."}
            
          else:
            result = {'status': "error",
                      'message': "Save unsuccessful. Please try again."}
        else:
          result = {'id': entity.key().id(), 
                    'status': "success",
                    'method': "add",
                    'en_type': "Sketch",
                    'data': jsonData} #this would also check if the json submitted was valid
      
      #If sketch was NOT created from latest version
      else:
        result = {'status': "error",
                  'message': "You cannot update an existing sketch from a previous version.",
                  'submessage': "You may still save it as a new sketch."}
      
    else:
      result = {'status': "error",
                'message': "Save unsuccessful. Please try again."}
    #except:
    #  result = {'status': "error",
    #            'message': "Save unsuccessful. Please try again."}
    
    return result
  
  #Gets Sketch entities by search criteria
  @staticmethod
  def get_entities(data, userid=""):
    utc = UTC()
    #update ModelCount when adding
    total_count = ModelCount.get_counter("Sketch_count")
    
    jsonData = json.loads(data)
    criteria = jsonData['criteria'].strip()
    show = jsonData['show']
    limit = long(jsonData['limit'])
    offset = long(jsonData['offset'])
    possible_names = []
    possible_users = []
    objects = []
    if criteria:
      possible_names = Sketch.get_matching_names(criteria)
      possible_users = User.get_matching_ids(criteria)
      
    objects = Sketch.all().order('-modified').fetch(limit=None)
    
    entities = []
    count = 0
    next_offset = 0
    
    if objects:
      for object in objects[offset:]:
        #Criteria Filter
        criteria_check = True
        if criteria:
          criteria_check = False
          if object.fileName in possible_names:
            criteria_check = True
          if object.owner in possible_users:
            criteria_check = True
        
        #Latest Version Filter
        latest_check = True
        if show == "latest":
          versionCount = VersionCount.get_counter(long(object.sketchId))
          if object.version < versionCount.lastVersion:
            latest_check = False
        
        #Check Permissions
        permissions = Permissions.user_access_control(object.sketchId,userid)
        user_name = User.get_name(object.owner)
        p_view = 0
        
        if criteria_check and latest_check and bool(permissions['p_view']):
          p_view = 1
        
          data = {'sketchId': object.sketchId,
                'version': object.version,
                'changeDescription': object.changeDescription,
                'fileName': object.fileName,
                'thumbnailData': object.thumbnailData,
                'owner': user_name,
                'owner_id': object.owner,
                'originalSketch': object.original_sketch,
                'originalVersion': object.original_version,
                'originalName': Sketch.get_sketch_name(object.original_sketch,object.original_version),
                'appver': object.appver,
                'p_view': p_view,
                'p_edit': bool(permissions['p_edit']),
                'p_comment': bool(permissions['p_comment']),
                'like': Like.get_entities_by_id(object.sketchId, 0)['count'],
                'comment': Comment.get_entities_by_id(object.sketchId)['count']}
            
          entity = {'id': object.key().id(),
                'created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'modified': object.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"), 
                'data': data}
          
          entities.append(entity)
          count += 1
          
        if count >= limit:
          next = objects.index(object) + 1
          if next < len(objects):
            next_offset = objects.index(object) + 1
          break
        
    result = {'method':'get_entities',
              'en_type': 'Sketch',
              'criteria': criteria,
              'total_count': total_count,
              'retrieve_type': show,
              'retrieved_count': count,
              'offset': offset,
              'limit': limit,
              'next_offset': next_offset,
              'entities': entities}
    return result

  #Gets Sketch entities by User ID
  @staticmethod
  def get_entities_by_id(data,userid=""):
    utc = UTC()
    #update ModelCount when adding
    theQuery = Sketch.all()
    #if model:
      #theQuery = theQuery.filter('model', model)
    
    jsonData = json.loads(data)
    criteria = long(jsonData['id'])
    show = jsonData['show']
    limit = long(jsonData['limit'])
    offset = long(jsonData['offset'])
    objects = theQuery.fetch(limit=None)

    entities = []
    count = 0
    next_offset = 0
    
    for object in objects[offset:]:
      if long(criteria) == object.owner:
        #Latest Version Filter
        latest_check = True
        if show == "latest":
          versionCount = VersionCount.get_counter(long(object.sketchId))
          if object.version < versionCount.lastVersion:
            latest_check = False
        #Check Permissions
        permissions = Permissions.user_access_control(object.sketchId,userid)
          
        if bool(permissions['p_view']) and latest_check:
          user_name = User.get_name(object.owner)
          data = {'sketchId': object.sketchId,
                'version': object.version,
                'changeDescription': object.changeDescription,
                'fileName': object.fileName,
                'thumbnailData': object.thumbnailData,
                'owner': user_name,
                'owner_id': object.owner,
                'originalSketch': object.original_sketch,
                'originalVersion': object.original_version,
                'originalName': Sketch.get_sketch_name(object.original_sketch,object.original_version),
                'appver': object.appver,
                'p_view': 1,
                'p_edit': bool(permissions['p_edit']),
                'p_comment': bool(permissions['p_comment']),
                'like': Like.get_entities_by_id(object.sketchId, 0)['count'],
                'comment': Comment.get_entities_by_id(object.sketchId)['count']}
          
          entity = {'id': object.key().id(),
                'created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'modified': object.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"), 
                'data': data}
          
          entities.append(entity)
          count += 1
            
        if limit != 0:
          if count >= limit:
            next = objects.index(object) + 1
            if next < len(objects):
              next_offset = objects.index(object) + 1
            break
    
    result = {'method':'get_entities_by_id',
              'en_type': 'Sketch',
              'count': count,
              'offset': offset,
              'limit': limit,
              'next_offset': next_offset,
              'entities': entities}
    return result

  #Gets a specific Sketch by SketchID and version
  @staticmethod
  def get_entity_by_versioning(data, purpose="View", userid=""):
    utc = UTC()
    versionmatch = True
    latestversion = True
    result = {'method':'get_entity_by_versioning',
                  'success':"no",
                  'id': 0,
                  'created': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                  'modified': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                  'data': ""
                  }
    
    try:
      jsonData = json.loads(data)
      sketchId = jsonData['id']
      version = jsonData['version']
      theobject = None
      
      versionCount = VersionCount.get_counter(long(sketchId))
      
      #Get latest version
      if versionCount and long(version) == -1:
        theobject = Sketch.all().filter('sketchId =', long(sketchId)).filter('version =', versionCount.lastVersion).get()
      #Get specific version
      elif long(version) != -1:
        theobject = Sketch.all().filter('sketchId =', long(sketchId)).filter('version =', long(version)).get()
        if theobject:
          if long(version) != versionCount.lastVersion:
            latestversion = False
        else:
          theobject = Sketch.all().filter('sketchId =', long(sketchId)).filter('version =', versionCount.lastVersion).get()
          versionmatch = False
      
      if theobject:
        #Check Permissions
        permissions = Permissions.user_access_control(theobject.sketchId,userid)
        
        #Check access type (view/edit):
        access = False
        if purpose == "Edit":
          access = bool(permissions['p_edit'])
        else:
          access = bool(permissions['p_view'])
        
        if access:
          user_name = User.get_name(theobject.owner)
          data = {'sketchId': theobject.sketchId,
                    'version': theobject.version,
                    'changeDescription': theobject.changeDescription,
                    'fileName': theobject.fileName,
                    'owner': user_name,
                    'owner_id': theobject.owner,
                    'fileData': theobject.fileData,
                    'thumbnailData': theobject.thumbnailData,
                    'originalSketch': theobject.original_sketch,
                    'originalVersion': theobject.original_version,
                    'originalName': Sketch.get_sketch_name(theobject.original_sketch,theobject.original_version),
                    'appver': theobject.appver,
                    'p_view': 1,
                    'p_edit': bool(permissions['p_edit']),
                    'p_comment': bool(permissions['p_comment']),
                    'p_public': Permissions.check_permissions(theobject.sketchId),
                    'groups': Sketch_Groups.get_groups_for_sketch(theobject.sketchId),
                    'ismatching': versionmatch,
                    'islatest': latestversion}
              
          result = {'method':'get_entity_by_versioning',
                    'en_type': 'Sketch',
                    'status':'success',
                    'id': theobject.key().id(),
                    'created': theobject.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                    'modified': theobject.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"), 
                    'data': data
                    }

        else:
          result = {'method':'get_entity_by_versioning',
                   'status':"Forbidden"}
      else:
        result = {'method':'get_entity_by_versioning',
                  'status':"Error"}
    except (RuntimeError, ValueError):
      result['data'] = ""
      
    return result

  #Gets Sketch entities by Group
  @staticmethod
  def get_entity_by_group(data,userid=""):
    utc = UTC()
    result = {}
    jsonData = json.loads(data)
    groupId = long(jsonData['id'])
    limit = long(jsonData['limit'])
    offset = long(jsonData['offset'])
    group_sketches = Sketch_Groups.get_sketches_for_group(long(groupId))
    entities = []
    count = 0
    next_offset = 0
    for g_s in group_sketches[offset:]:
      sketch_id = long(g_s['sketch_id'])
      permissions = Permissions.user_access_control(sketch_id, userid)
      
      if permissions['p_view']:
        versionCount = VersionCount.get_counter(sketch_id)
        theobject = Sketch.all().filter('sketchId',sketch_id).filter('version',long(versionCount.lastVersion)).get()
        user_name = User.get_name(theobject.owner)
        data = {'sketchId': theobject.sketchId,
                  'version': theobject.version,
                  'changeDescription': theobject.changeDescription,
                  'fileName': theobject.fileName,
                  'owner': user_name,
                  'owner_id': theobject.owner,
                  'thumbnailData': theobject.thumbnailData,
                  'originalSketch': theobject.original_sketch,
                  'originalVersion': theobject.original_version,
                  'originalName': Sketch.get_sketch_name(theobject.original_sketch,theobject.original_version),
                  'appver': theobject.appver,
                  'p_view': 1,
                  'p_edit': bool(permissions['p_edit']),
                  'p_comment': bool(permissions['p_comment']),
                  'g_edit': bool(g_s['edit']),
                  'g_comment': bool(g_s['comment']),
                  'like': Like.get_entities_by_id(theobject.sketchId, 0)['count'],
                  'comment': Comment.get_entities_by_id(theobject.sketchId)['count']}
                
        entity = {'id': theobject.key().id(),
              'created': theobject.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
              'modified': theobject.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"), 
              'data': data}
        entities.append(entity)
        count += 1
        
      if count >= limit:
        next = group_sketches.index(g_s) + 1
        if next < len(group_sketches):
          next_offset = group_sketches.index(g_s) + 1
        break
    result = {'method':'get_entity_by_group',
              'en_type': "Sketch",
              'count': count,
              'limit': limit,
              'offset': offset,
              'next_offset': next_offset,
              'entities': entities}
    return result
  
  #Checks if a Sketch entity belongs to a particular User
  @staticmethod
  def check_if_owner(id = 0, user_id = 0):
    is_owner = False
    try:
      if long(user_id) != 0:
        versionCount = VersionCount.get_counter(id)
        object = Sketch.all().filter('sketchId',id).filter('version',long(versionCount.lastVersion)).get()
        if object:
          if object.owner == long(user_id):
            is_owner = True
    except ValueError:
      is_owner = False
    return is_owner
  
  #Gets the name of a Sketch entity
  @staticmethod
  def get_sketch_name(sketchId=-1,version=-1):
    try:
      object = Sketch.all().filter('sketchId =', long(sketchId)).filter('version =', long(version)).get()
      if object:
        return object.fileName
      else:
        return "N/A"
    except:
      return "N/A"
      
  #Gets the names of Sketches that match the given criteria
  @staticmethod
  def get_matching_names(criteria=""):
    theQuery = Sketch.all()
    objects = theQuery.run()
    entities = []
    if criteria != "":
      for object in objects:
        if criteria.lower() in object.fileName.lower():
          entities.append(object.fileName)
          
    return entities
  
  #Counts the number of Sketch entities that a particular User may #View/Edit/Comment
  @staticmethod
  def count_permitted(user_id=0, permission_type="View"):
    query = Sketch.all()
    objects = query.run()
    
    count = 0
    for object in objects:
      permissions = Permissions.user_access_control(object.key().id(),user_id)
      if permission_type == "View":
        if bool(permissions['p_view']):
          count = count + 1
      if permission_type == "Edit":
        if bool(permissions['p_edit']):
          count = count + 1
      if permission_type == "Comment":
        if bool(permissions['p_comment']):
          count = count + 1
    return count
    
  #Deletes a specific Sketch entity.
  #You can't name it delete since db.Model already has a delete method
  @staticmethod
  def remove(sketch_id, version, user_id):
    #Only the sketch owner or an admin may delete the sketch
    can_delete = False
    is_admin = User.check_if_admin(user_id)
    is_owner = Sketch.check_if_owner(long(sketch_id), user_id)
    if is_owner:
      can_delete = True
    elif is_admin:
      can_delete = True
      
    if can_delete:
      entity = Sketch.all().filter('sketchId',sketch_id).filter('version',version).get()
      
      if entity:
        appver = entity.appver
        fileName = entity.fileName
        owner = entity.owner
        check_original = False
        if entity.sketchId == entity.original_sketch:
          if entity.version == entity.original_version:
            check_original = True
            
        entity.delete()
        ModelCount.decrement_counter('Sketch_count')
        AppVersionCount.decrement_counter(appver, check_original)
        Comment.delete_by_sketch(long(sketch_id))
        Permissions.delete_by_sketch(long(sketch_id))
        Sketch_Groups.delete_by_sketch(long(sketch_id))
        Like.delete_by_sketch(long(sketch_id))
        
        if is_admin and not is_owner:
          
          Notification.add(owner, "ADMINDELETE", 0, fileName, 0)
    
        result = {'method':'remove',
                  'id': sketch_id,
                  'status': 'success'
                    }
      else:
          result = {'method':'remove',
                    'id': sketch_id,
                    'status': 'error'}
          
    else:
      result = {'method':'remove',
                    'id': sketch_id,
                    'status': 'error'}
    
    return result

  #Edits a specific Sketch entity. Currently not used.
  @staticmethod
  def edit_entity(sketch_model_id, data):
    jsonData = json.loads(data)
    entity = Sketch.get_by_id(long(sketch_model_id))
    
    if jsonData['sketchId']!='':
      entity.sketchId=long(jsonData['sketchId'])
    if jsonData['version']!='':
      entity.version=long(jsonData['version'])
    if jsonData['changeDescription']!='':
      entity.changeDescription=jsonData['changeDescription']
    if jsonData['fileName']!='':
      entity.fileName=jsonData['fileName']
    if jsonData['owner']!='':
      entity.owner=long(jsonData['owner'])
    if jsonData['fileData']!='':
      entity.fileData=jsonData['fileData']
    if jsonData['thumbnail']!='':
      entity.thumbnailData=jsonData['thumbnail']
    if jsonData['originalSketch']!='':
      entity.original_sketch=long(jsonData['originalSketch'])
    if jsonData['originalVersion']!='':
      entity.original_version=long(jsonData['originalVersion'])
    if jsonData['appver']!='':
      entity.appver=float(jsonData['appver'])
    entity.put()
    
    result = {'id': entity.key().id(), 
              'data': json.dumps(jsonData) #this would also check if the json submitted was valid
              }
    return result
    
#Imports placed below to avoid circular imports
from rpx import User, UTC
from counters import ModelCount, VersionCount, AppVersionCount
from comments_likes import Comment, Like
from permissions_groups import Permissions, Sketch_Groups
from notifications import Notification    
