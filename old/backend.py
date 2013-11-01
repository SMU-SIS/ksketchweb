"""Backend Module

@created: Goh Kian Wei (Brandon)
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
from rpx import User
from rpx import AppUserCount

"""
Attributes and functions for Sketch entity
"""

class UTC(datetime.tzinfo):
  def utcoffset(self, dt):
    return datetime.timedelta(hours=0)
    
  def dst(self, dt):
    return datetime.timedelta(0)
    
  def tzname(self, dt):
    return "UTC"

#Handles Sketch data, and saving and loading of sketches
class Sketch(db.Model):
  #Use backend record id as the model id for simplicity
  sketchId = db.IntegerProperty(required=True)
  version = db.IntegerProperty(required=True)
  changeDescription = db.StringProperty()
  fileName = db.StringProperty(required=True)
  owner = db.IntegerProperty(required=True)
  fileData = db.TextProperty(required=True)
  thumbnailData = db.TextProperty()
  original_sketch = db.IntegerProperty(required=True) #might be changed
  original_version = db.IntegerProperty(required=True)
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
    group_sketches = Sketch_Groups.get_sketches_for_group(long(groupId))
    entities = []
    count = 0
    for g_s in group_sketches:
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
    result = {'method':'get_entity_by_group',
              'en_type': "Sketch",
              'count': count,
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
    
#Counter increment for Sketch ID and Sketch Count.
class ModelCount(db.Model):
  en_type = db.StringProperty(required=True,default='Default-entype')
  count = db.IntegerProperty(required=True, default=0)
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
  
  @staticmethod
  def get_counter(en_type):
    return ModelCount.all().filter('en_type',en_type).get()
  
  @staticmethod
  def increment_counter(en_type):
    modelCount = ModelCount.all().filter('en_type',en_type).get()
    if modelCount:
      modelCount.count += 1
      modelCount.put()
    else:
      modelCount = ModelCount(en_type='Sketch', count=1)
      modelCount.put()
      
  @staticmethod
  def decrement_counter(en_type):
    modelCount = ModelCount.all().filter('en_type',en_type).get()
    if modelCount:
      modelCount.count -= 1
      modelCount.put()

#Counter increment for version numbers for each Sketch ID.
class VersionCount(db.Model):
  sketchId = db.IntegerProperty(required=True, default=0)
  lastVersion = db.IntegerProperty(required=True, default=0)
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
  
  @staticmethod
  def get_counter(sketchId = -1):
    return VersionCount.all().filter('sketchId', long(sketchId)).get()
  
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
  app_version = db.FloatProperty()
  sketch_count = db.IntegerProperty()
  original_count = db.IntegerProperty()
  

  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
  
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
      
  
  @staticmethod  
  def decrement_counter(app_version = -1, original = True):
    appVersionCount = AppVersionCount.all().filter('app_version', float(app_version)).get()
    if appVersionCount:
      appVersionCount.sketch_count -= 1
      if original:
        appVersionCount.original_count -= 1
      appVersionCount.put()
  
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
            
      appuser_query = AppUserCount.all().filter('app_version', float(object.app_version)).get()
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


#Handles Comment data, and creation of comments
class Comment(db.Model):
  sketch_id = db.IntegerProperty()
  user_id = db.IntegerProperty(required=True)
  content = db.StringProperty(required=True)
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
    #update ModelCount when adding
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
    #update ModelCount when adding
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
      
class Permissions(db.Model):
  sketch_id = db.IntegerProperty()
  view = db.BooleanProperty(required=True)
  edit = db.BooleanProperty(required=True)
  comment = db.BooleanProperty(required=True)
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
       
  @staticmethod
  def add(s_id, p_view, p_edit, p_comment):
    p_key = -1
    try:
      entity = Permissions.all().filter('sketch_id',long(s_id)).get()
      #Update existing permissions
      if entity:
        entity.view = bool(p_view)
        entity.edit = bool(p_edit)
        entity.comment = bool(p_comment)
        entity.put()
        
      #No existing permissions - create new permissions
      else:
        entity = Permissions(sketch_id = long(s_id),
                            view = bool(p_view),
                            edit = bool(p_edit),
                            comment = bool(p_comment))
        entity.put()
      p_key = entity.key().id()
    except:
      p_key = -1
    return p_key
    
  @staticmethod
  def check_permissions(sketch_id = 0):
    result = {'p_view':False,
              'p_edit':False,
              'p_comment':False}
              
    permissions = Permissions.all().filter('sketch_id', sketch_id).get()
    if permissions:
      result = {'p_view':permissions.view,
                'p_edit':permissions.edit,
                'p_comment':permissions.comment}
    return result
    
  @staticmethod
  def user_access_control(sketch_id = 0, user_id = 0):
    permissions = {'p_view':False,
                    'p_edit':False,
                    'p_comment':False}
    #Check if Admin - if true, grant FULL access
    if User.check_if_admin(user_id):
      permissions = {'p_view':True,
                    'p_edit':True,
                    'p_comment':True}
    #Check if Owner - if true, grant FULL access
    elif Sketch.check_if_owner(long(sketch_id), user_id):
      permissions = {'p_view':True,
                    'p_edit':True,
                    'p_comment':True}
    else:
      #Retrieve public permissions
      permissions = Permissions.check_permissions(long(sketch_id))
      
      #Retrieve group permissions
      group_permissions = Sketch_Groups.get_groups_for_sketch(long(sketch_id))
      user_groups = UserGroupMgmt.get_memberships(user_id)
      user_group_permissions = []
      for u_g in user_groups:
        group_id = u_g['group_id']
        for g_p in group_permissions:
          if long(group_id) == long(g_p['id']):
            user_group_permissions.append(g_p)
      #Apply group permissions
      for u_g_p in user_group_permissions:
        permissions['p_view'] = True
        if not permissions['p_edit']:
          permissions['p_edit'] = u_g_p['edit']
        if not permissions['p_comment']:
          permissions['p_comment'] = u_g_p['comment']
        if permissions['p_edit'] and permissions['p_comment']:
          break
    return permissions
    
  @staticmethod  
  def delete_by_sketch(sketch_id):
    theQuery = Permissions.all()
    theQuery = theQuery.filter('sketch_id =', long(sketch_id))
    theobject = theQuery.get()
    if theobject:
      theobject.delete()
    result = {'method':'delete_by_sketch',
              'en_type': 'Permissions',
              'sketchId': sketch_id}
    return result 
    
class Sketch_Groups(db.Model):
  sketch_id = db.IntegerProperty()
  group_id = db.IntegerProperty(required=True)
  edit = db.BooleanProperty(required=True)
  comment = db.BooleanProperty(required=True)
  #It is assumed that a sketch that belongs to a group
  #can be viewed by said group - thus, a "view" variable is
  #unnecessary.
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
       
  @staticmethod
  def add(s_id, group_permissions):
    count = 0
    current_perm = Sketch_Groups.all().filter('sketch_id', long(s_id)).fetch(limit=None)
    for c_p in current_perm:
      c_p.delete()
    try:
      for g_p in group_permissions:
        edit = False
        comment = False
        try:
          edit = bool(g_p['edit'])
        except (KeyError, ValueError):
          edit = False
        try:
          comment = bool(g_p['comment'])
        except (KeyError, ValueError):
          edit = False
          
        new_perm = Sketch_Groups(sketch_id = long(s_id),
                            group_id = long(g_p['id']),
                            edit = edit,
                            comment = comment)
        new_perm.put()
        count += 1
    except:
      count = 0
    return count
  
  @staticmethod
  def get_groups_for_sketch(sketch_id=0):
    theQuery = Sketch_Groups.all()
    objects = theQuery.run()
    
    entities = []
    for object in objects:
      if object.sketch_id == sketch_id:
        data = {'group_name': Group.get_name(object.group_id)}
        entity = {'object_id': object.key().id(),
                  'sketch_id': object.sketch_id,
                  'id': object.group_id,
                  'data':data,
                  'edit': object.edit,
                  'comment':object.comment}
        entities.append(entity)
    return entities    
  
  @staticmethod
  def get_sketches_for_group(group_id=0):
    theQuery = Sketch_Groups.all()
    objects = theQuery.run()
    
    entities = []
    for object in objects:
      if object.group_id == group_id:
        data = {'id': object.key().id(),
                'sketch_id': object.sketch_id,
                'group_id': object.group_id,
                'group_name': Group.get_name(object.group_id),
                'edit': object.edit,
                'comment':object.comment}
        entities.append(data)
    return entities
    
  @staticmethod  
  def delete_by_sketch(sketch_id):
    theQuery = Sketch_Groups.all()
    theQuery = theQuery.filter('sketch_id', long(sketch_id))
    objects = theQuery.run()
    count = 0
    for object in objects:
      object.delete()
      count += 1
    result = {'method':'delete_by_sketch',
              'en_type': 'Sketch_Groups',
              'sketchId': sketch_id,
              'count': count}
    return result
    
  @staticmethod  
  def delete_by_group(group_id):
    theQuery = Sketch_Groups.all()
    theQuery = theQuery.filter('group_id', long(group_id))
    objects = theQuery.run()
    count = 0
    for object in objects:
      object.delete()
      count += 1
    result = {'method':'delete_by_group',
              'en_type': 'Sketch_Groups',
              'groupId': group_id,
              'count': count}
    return result
    
class Group(db.Model):
  group_name = db.StringProperty(required=True)
  group_sketches = db.TextProperty()
  created = db.DateTimeProperty(auto_now_add=True) #The time that the model was created
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d

  @staticmethod
  def add(data):
    #update ModelCount when adding
    theQuery = Group.all()
    jsonData = json.loads(data)
    result = {'status':'error',
              'message':'There was an error in creating your group.',
              'submessage':'Please try again later.'}    
    if jsonData['group_name'] != '':
      if jsonData['user_id'] != '':
        
        objects = theQuery.run()
        group_exists = False
        for object in objects:
          if jsonData['group_name'] == object.group_name:
            group_exists = True
            break
        if not group_exists:
          entity = Group(group_name=jsonData['group_name'])
        
          entity.put()
          
          usergroupmgmt = UserGroupMgmt(user_id=int(jsonData['user_id']),
                                        group_id=entity.key().id(),
                                        role="Founder")
          usergroupmgmt.put()
        
          result = {'status': 'success',
                    'method': 'add',
                    'en_type': 'Group',
                    'g_name': jsonData['group_name'],
                    'u_id': jsonData['user_id'],
                    'role': "Founder"}
        else:
          result = {'status': 'error',
                    'message': 'The name you chose is already in use!',
                    'submessage': 'Please choose a different group name!'}
              
    return result
    
  @staticmethod
  def get_name(model_id):
    try:
      entity = Group.get_by_id(int(model_id))
      
      if entity:
        return entity.group_name
      else:
        return "N/A"
    except ValueError:
      return "N/A"
      
  @staticmethod
  def get_entities(data):
    jsonData = json.loads(data)
    criteria = long(jsonData['id'])
    utc = UTC()
    theQuery = UserGroupMgmt.all()
    objects = theQuery.run()
    group = ""
    entities = []
    for object in objects:
      include = True
      if criteria != "":
        #Change this soon!
        if int(criteria) == object.user_id:
          include = True
        else:
          include = False
          
        if object.role == "Pending":
          include = False
          
      if include:
        group = Group.get_name(object.group_id)
        data = {'group_name': group,
              'user': object.user_id, #placeholder
              'role': object.role}
        entity = {'id': object.group_id, 
              'data': data}
        entities.append(entity)
    result = {'method':'get_entities',
              'en_type': 'Group',
              'entities': entities}
    return result
    
  @staticmethod
  def get_entity(data):
    jsonData = json.loads(data)
    model_id = long(jsonData['id'])
    utc = UTC()
    result = {}
    theobject = Group.get_by_id(long(model_id))
    if theobject:
      user_groups_query = UserGroupMgmt.all().filter('group_id', theobject.key().id()).run()
      u_groups = []
      
      if user_groups_query:
        for u_g in user_groups_query:
          user_name = User.get_name(u_g.user_id)
          u_entity = {'user': user_name,
                      'g_hash': User.get_image(u_g.user_id),
                      'user_id': u_g.user_id,
                      'group_id': model_id,#placeholder
                      'role': u_g.role}
          u_groups.append(u_entity)    
      
      result = {'status':'success',
                'method':'get_entity',
                'en_type': 'Group',
                'id': model_id,
                'group_name': theobject.group_name,
                'u_groups': u_groups
                }
    else:
      result = {'status':'Error',
                'message':'There was an error in loading the group you wanted.',
                'submessage':'Please check the URL and try again later.'}
    return result
    
  @staticmethod
  def check_users(data):
  
    jsonData = json.loads(data)
    model_id = long(jsonData['id'])
    criteria = jsonData['criteria'].strip()
    
    theQuery = User.all()
    objects = theQuery.run()
    
    groupQuery = UserGroupMgmt.all().filter('group_id', int(model_id))
    groupObjects = groupQuery.fetch(limit=None)
    
    entities = []
    for object in objects:
      test = ""
      include = True
      if criteria != "":      
        if criteria.lower() in object.display_name.lower():
          include = True
        else:
          include = False
      
      for groupObject in groupObjects:
        test += " " + str(groupObject.user_id)
        if object.key().id() == groupObject.user_id:
          include = False
            
      if include:
        data = {'id': object.key().id(),
                'u_name': object.display_name,
                'u_realname': object.real_name}
        entities.append(data)
    return entities
   
  @staticmethod
  def remove(data, userid):
    jsonData = json.loads(data)
    model_id = long(jsonData['id'])
    
    theobject = Group.get_by_id(long(model_id))
    
    check_founder = UserGroupMgmt.all().filter('group_id', model_id).filter('role', "Founder").get()
    result = {}
    if theobject and check_founder:
      can_delete = False
      if check_founder.user_id == userid:
        can_delete = True
        
      if can_delete:
        group_name = theobject.group_name
        theobject.delete()
        user_groups_query = UserGroupMgmt.all().filter('group_id', model_id).run()
        
        pending = Notification.all().filter('notification_type','GROUPINVITE').run()
        
        for p in pending:
          u_g = UserGroupMgmt.get_by_id(p.relevant_id)
          if u_g and u_g.group_id == model_id:
            p.notification_type = 'GROUPDELCANCEL'
            p.other_info = group_name
            p.n_date = datetime.datetime.now()
            p.put()
        
        Sketch_Groups.delete_by_group(model_id)
        
        for u_g in user_groups_query:
          
          if u_g.role == 'Member':
            Notification.add(u_g.user_id, "GROUPDELETE", userid, group_name, 0)
          u_g.delete()
        result = {'status': 'success',
                  'method': 'remove',
                  'en_type': 'Group',
                  'message': "The group '" + group_name + "' has been successfully deleted."}
      else:
        result = {'status': 'Error',
                  'message': "You have to be the Founder in order to delete the group." }
    else:
      result = {'status': 'Error',
                'message': "Unable to delete the group!"}
    return result
    
class UserGroupMgmt(db.Model):
  user_id = db.IntegerProperty(required=True)
  group_id = db.IntegerProperty(required=True)
  role = db.StringProperty(required=True)
  
  @staticmethod
  def add(data, other_user):
    #update ModelCount when adding
    jsonData = json.loads(data)
    result = {'status':'error',
              'message':'There was an error in sending the invite.',
              'submessage':'Please try again later.'}    
    if jsonData['group_id'] != 0:
      users = jsonData['users']
      invited = []
      theQuery = UserGroupMgmt.all().filter('group_id', long(jsonData['group_id']))
      objects = theQuery.fetch(limit=None)
      for user in users:
        user_group_exists = False
        for object in objects:
          if long(user['id']) == long(object.user_id):
            user_group_exists = True
            break
        if not user_group_exists:
          entity = UserGroupMgmt(user_id=long(user['id']),
                                group_id=long(jsonData['group_id']),
                                role="Pending")
        
          entity.put()
          
          Notification.add(long(user['id']), "GROUPINVITE", long(other_user), "",entity.key().id()) 
          invited.append(user['u_name'])
      
      if len(invited) > 0:
        result = {'status': 'success',
              'invited': invited,
              'group_id': jsonData['group_id']}  
      else:
        result = {'status':'error',
                'message':'Please select valid user(s) to invite.'}   
        
    else:
      result = {'status':'error',
              'message':'Please select valid user(s) to invite.'}   
    return result
    
  @staticmethod
  def remove_user(data, userid):
    jsonData = json.loads(data)
    remove_id = long(jsonData['user_id'])
    role = jsonData['role']
    group_id = long(jsonData['group_id'])
    
    result = {}
    
    user_groups_query = UserGroupMgmt.all().filter('group_id', group_id).filter('user_id', remove_id).get()
    check_founder = UserGroupMgmt.all().filter('group_id', group_id).filter('role', "Founder").get()
    
    if user_groups_query and check_founder:
      if check_founder.user_id == userid or User.check_if_admin(userid):
        if userid != remove_id:
          user_groups_query.delete()
          result = {'status': 'success',
                    'method': 'remove_user',
                    'en_type': 'UserGroupMgmt',
                    'type': 'kick',
                    'message': 'You have expelled ' + User.get_name(remove_id) + ' the group "' + Group.get_name(group_id) + '".'}
          Notification.add(remove_id, "GROUPEXPEL", userid, "", group_id)
        else:
          result = {'status': 'Error',
                    'message': 'You cannot expel yourself if you are the Founder!',
                    'submessage': 'Pass the Founder position to someone else before trying to leave.'}
      elif remove_id == userid:
        user_groups_query.delete()
        result = {'status': 'success',
                  'method': 'remove_user',
                  'en_type': 'UserGroupMgmt',
                  'type': 'quit',
                  'message': 'You have left the group "' + Group.get_name(group_id) + '".'}
        Notification.add(check_founder.user_id, "GROUPLEAVE", remove_id, "", group_id) 
        
      else:
        result = {'status': 'Error',
                  'message': 'You cannot expel a member unless you are the founder!'}
    else:
      result = {'status': 'Error',
                'message': 'Unable to find the user to be expelled!'}
    return result
    
  @staticmethod
  def pass_founder(data, userid):
    jsonData = json.loads(data)
    pass_id = long(jsonData['user_id'])
    role = jsonData['role']
    group_id = long(jsonData['group_id'])
    
    result = {}
    
    user_groups_query = UserGroupMgmt.all().filter('group_id', group_id).filter('user_id', pass_id).get()
    check_founder = UserGroupMgmt.all().filter('group_id', group_id).filter('role', "Founder").get()
  
    if user_groups_query and check_founder:
      if check_founder.user_id == userid:
        if userid != pass_id:
          user_groups_query.role = "Founder";
          check_founder.role = "Member";
          user_groups_query.put()
          check_founder.put()
          
          
          Notification.add(pass_id, "GROUPPASSFOUNDER", check_founder.user_id, "", group_id) 
          result = {'status': 'Success',
                    'method': 'pass_founder',
                    'en_type': 'UserGroupMgmt',
                    'message': 'You have made ' + User.get_name(pass_id) + ' the Founder of the group "' + Group.get_name(group_id) + '".'}
        else:
          result = {'status': 'Error',
                  'message': 'You are already the Founder!'}
      else:
        result = {'status': 'Error',
                  'message': 'You are not the Founder of this group!'}
    else:
      result = {'status': 'Error',
                  'message': 'Unable to find the user to be given the Founder position!'}
    return result
  @staticmethod
  def get_memberships(userid):
    entities = []
    try:
      theQuery = UserGroupMgmt.all().filter('user_id', long(userid))
      objects = theQuery.run()
      for object in objects:
        if object.role != "Pending":
          data = {'user_id': object.user_id,
                  'group_id': object.group_id,
                  'role': object.role}
          entities.append(data)
    except ValueError:
      entities = []
    return entities
    
  @staticmethod
  def accept_reject(data, userid):
    jsonData = json.loads(data)
    result = {'status':'error',
              'message':'There was an error in processing the invitation.',
              'submessage':'Please try again later.'}
    status = str(jsonData['status'])
    u_g = UserGroupMgmt.get_by_id(int(jsonData['u_g']))
    founder = UserGroupMgmt.all().filter('group_id', u_g.group_id).filter('role', 'Founder').get()
    if status == "accept":
      u_g.role = "Member"
      u_g.put()
      Notification.add(founder.user_id, "GROUPACCEPT", int(userid), "", u_g.group_id)
      Notification.add(int(userid), "GROUPJOINCFM", 0, "", u_g.group_id)  
    else:
      u_g.delete()
      Notification.add(founder.user_id, "GROUPREJECT", int(userid), "", u_g.group_id) 
    
    old_notify = Notification.get_by_id(int(jsonData['n_id']))
    old_notify.delete()
    
    result = {'status': 'success',
              'method': 'accept_reject',
              'en_type': 'UserGroupMgmt',
              'message': 'You have successfully ' + jsonData['status'] + 'ed the group invitation.'}
    return result
      
class Notification(db.Model):
  user_id = db.IntegerProperty(required=True)
  notification_date = db.DateTimeProperty(auto_now_add=True)
  notification_type = db.StringProperty()
  other_user = db.IntegerProperty()
  # other_info = db.StringProperty()
  relevant_id = db.IntegerProperty()
  message = db.StringProperty()

  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
       
  @staticmethod
  def add(u_id=-1, type="", o_user = 0, o_info = "", r_id = 0):
    if u_id != -1 and type != "":
      #Notification creation
      o_user_name = User.get_name(o_user)
      verify = False
      if type == "GROUPINVITE":
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
      elif type == "GROUPACCEPT":
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = r_id,
                              message = o_user_name + " has accepted your invitation to the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPREJECT":
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = r_id,
                              message = o_user_name + " has rejected your invitation to the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPLEAVE":
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = r_id,
                              message = o_user_name + " has left the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPJOINCFM":
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = 0,
                              relevant_id = r_id,
                              message = "You have joined the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPPASSFOUNDER":
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = r_id,
                              message = o_user_name + " has made you the Founder of the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPEXPEL":
        relevant =  Group.get_name(r_id)
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = r_id,
                              message = o_user_name + " has kicked you from the group " + relevant + ".")
        notify.put()
        verify = True
      elif type == "GROUPDELETE":
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = 0,
                              message = o_user_name + " has deleted the group " + o_info + ".")
        notify.put()
        verify = True
      elif type == "GROUPDELCANCEL":
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = o_user,
                              relevant_id = 0,
                              message = o_user_name + " has cancelled your invite and deleted the group " + o_info + ".")
        notify.put()
        verify = True               
      elif type == "ADMINDELETE":
        notify = Notification(user_id = u_id,
                              notification_type = type,
                              other_user = 0,
                              relevant_id = 0,
                              message = "An administrator has deleted your sketch '" + o_info + "'.")
        notify.put()
        verify = True
      return verify
       
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
      
class Like(db.Model):
  sketch_id = db.IntegerProperty()
  user_id = db.IntegerProperty(required=True)
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
    
class ActionHandler(webapp2.RequestHandler):
    """Class which handles bootstrap procedure and seeds the necessary
    entities in the datastore.
    """
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

    def add_sketch(self): #/add/sketch
    
        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
          
        result = Sketch.add(self.request.body, userid=userid)
        return self.respond(result)

    def delete_sketch(self, model_id):  #/delete/sketch/<model_id>

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
        result = Sketch.remove(model_id, userid)
        
        return self.respond(result)
          
    def user_sketch(self): #/list/sketch/user

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
          
        result = Sketch.get_entities_by_id(self.request.body,userid=userid)
        return self.respond(result)    
          
    def group_sketch(self): #/list/sketch/group

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
          
        result = Sketch.get_entity_by_group(self.request.body,userid=userid)
        return self.respond(result)    
        
      
    def list_sketch(self): #/list/sketch

        offset = 0
        new_offset = self.request.get("offset")
        if new_offset:
          offset = int(new_offset)

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
          
        result = Sketch.get_entities(self.request.body, userid=userid)
        return self.respond(result)
      
    def view_sketch(self): #/get/sketch/view

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
        
        result = Sketch.get_entity_by_versioning(self.request.body, "View", userid=userid)
        return self.respond(result)    
        
    def edit_sketch(self): #/get/sketch/edit

        auser = self.auth.get_user_by_session()
        userid = 0
        if auser:
          userid = auser['user_id']
        
        result = Sketch.get_entity_by_versioning(self.request.body, "Edit", userid=userid)
        return self.respond(result) 
        
    def add_group(self):
        if self.request.method=="POST":
          result = Group.add(self.request.body)
          return self.respond(result)
    
        else:
          data = self.request.get("obj")
          if data: 
            result = Group.add(data)
          return self.respond(result)

    def get_group(self):

        result = Group.get_entity(self.request.body)
        return self.respond(result) 

    def user_group(self):

        offset = 0
        new_offset = self.request.get("offset")
        if new_offset:
          offset = int(new_offset)

        result = Group.get_entities(self.request.body)
        return self.respond(result)

    def check_user_group(self):
      result = {'status':'error',
                'message':''}
      entities = Group.check_users(self.request.body)
      result = {'status':'success',
                'method':'list_user',
                'en_type': 'User',
                'entities': entities}
      return self.respond(result)
        
    def get_versions(self):

        offset = 0
        new_offset = self.request.get("offset")
        if new_offset:
          offset = int(new_offset)

        result = AppVersionCount.retrieve_by_version()
        return self.respond(result)
        
    def add_user_group(self):
        auser = self.auth.get_user_by_session()
        result = {'status':'error',
              'message':'There was an error in sending the invite.',
              'submessage':'Please try again later.'}    
        if auser:
          userid = auser['user_id']
          result = UserGroupMgmt.add(self.request.body, userid)
        return self.respond(result)
        
    def remove_user_group(self):
        auser = self.auth.get_user_by_session() 
        if auser:
          userid = auser['user_id']
          result = UserGroupMgmt.remove_user(self.request.body, userid)
        return self.respond(result)   
        
    def pass_founder_group(self):
        auser = self.auth.get_user_by_session() 
        if auser:
          userid = auser['user_id']
          result = UserGroupMgmt.pass_founder(self.request.body, userid)
        return self.respond(result)        
        
    def accept_reject_group(self):
        auser = self.auth.get_user_by_session()
        result = {'status':'error',
              'message':'Not authenticated.'}
        if auser:
          userid = auser['user_id']
          result = UserGroupMgmt.accept_reject(self.request.body, userid)
        return self.respond(result) 
        
    def delete_group(self):
        auser = self.auth.get_user_by_session()
        result = {'status':'error',
              'message':'Not authenticated.'}
        if auser:
          userid = auser['user_id']
          result = Group.remove(self.request.body, userid)
        return self.respond(result)      
        
    def get_notification(self, limit):
        auser = self.auth.get_user_by_session()
        result = {}
        if auser:
          userid = auser['user_id']
          result = Notification.get_entities(userid, limit)
        return self.respond(result)
        

    def get_all_notification(self):
        auser = self.auth.get_user_by_session()
        result = {}
        if auser:
          userid = auser['user_id']
          result = Notification.get_entities(userid)
        return self.respond(result)        
          
    def add_comment(self):
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
        
    def get_comment(self):
        auser = self.auth.get_user_by_session()
        if auser:
          userid = auser['user_id']
        result = Comment.get_entities_by_id_handler_wrapper(self.request.body)
        return self.respond(result) 
          
    def toggle_like(self):
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
        
    def get_like(self):
        
        auser = self.auth.get_user_by_session()
        if auser:
          userid = auser['user_id']
          result = Like.get_entities_by_id_handler_wrapper(self.request.body, userid)
        else:
          result = Like.get_entities_by_id_handler_wrapper(self.request.body, 0)
        return self.respond(result)    
   
        
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
