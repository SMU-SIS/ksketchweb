'''
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
'''

"""Backend Module

@created: Goh Kian Wei (Brandon), Kevin Koh, Shannon Lim, Tony Tran, Samantha Wee, Wong Si Hui
@code_adapted_from: Chris Boesch, Daniel Tsou
"""
"""
Note to self: json.loads = json string to objects. json.dumps is object to json string.
"""     
import datetime
import urllib
import os
import urllib
import urllib2
import logging
import webapp2
from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from urlparse import parse_qsl
import json
from google.appengine.ext import deferred

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
  isLatest = db.BooleanProperty(default=True)
  overwrite = False
  lowerFileName = db.StringProperty(default="")
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d

  #Creates a new Sketch entity from solving discrepancy
  @staticmethod
  def addDiscrepancy(data, userid):
    result = {}

    jsonData = json.loads(data)

    v_count = VersionCount.get_counter(long(jsonData['sketchId']))
    
    try:
      jsonData = json.loads(data)
      theobject = None
      
      versionCount = VersionCount.get_and_increment_counter(long(jsonData['sketchId']))
      jsonData['version'] = str(versionCount)
      versionCount_decrement = versionCount - 1
      change = jsonData['changeDescription']
      change = change[:255]
      Sketch.update_latest_flag(jsonData['sketchId'])
      entity = Sketch(sketchId=long(jsonData['sketchId']),
                    version=long(jsonData['version']),
                    changeDescription=change,
                    fileName=jsonData['fileName'],
                    owner=long(jsonData['owner_id']),
                    fileData=jsonData['fileData'],
                    thumbnailData=jsonData['thumbnailData'],
                    original_sketch=long(jsonData['originalSketch']),
                    original_version=long(versionCount_decrement),
                    appver=float(jsonData['appver']),
                    lowerFileName=jsonData['fileName'].lower())
     
      verify = entity.put()
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
    except:
      result = {'status': "error",
              'message': "Save unsuccessful. Please try again."}

    return result

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
      #Check if the sketch is a new sketch
      check_new_sketch=False
      ModelCount.increment_counter('Sketch_count')
      #For new sketches/sketches saved as new sketches
      if jsonData['sketchId'] == "" or jsonData['sketchId'] == -1 or jsonData['sketchId'] == None:
        #Assigns new SketchId
        handmade_key = db.Key.from_path('Sketch', 1)
        #Get new ID from DB
        new_ids = db.allocate_ids(handmade_key, 1)
        check_new_sketch=True
        modelCount = new_ids[0]
        ModelCount.increment_counter('Sketch')
        logging.info("Model count : " + str(modelCount))
        jsonData['sketchId'] = str(modelCount)
      
      #Placeholder for current version of SketchId
      versionCount = 0
      modelCount=int(jsonData['sketchId'])
      #If sketch is completely original (i.e. new sketch)
      if jsonData['originalSketch'] == -1:
        check_original = True
        #Creates new version counter for the new Sketch.
        versionCount = VersionCount.get_and_increment_counter(long(jsonData['sketchId']))
        jsonData['originalVersion'] = versionCount
        jsonData['originalSketch'] = str(modelCount)
        
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
          #If overwrite status is true, force old sketch to overwrite the new one
          check_if_latest = False
          thelatestobject = Sketch.all().filter('sketchId =', long(jsonData['sketchId'])).filter('version =', v_count.lastVersion).get()
          thelatestobject_created = thelatestobject.created
        Sketch.update_latest_flag(jsonData['sketchId'])
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
        if(check_new_sketch):
          new_key = db.Key.from_path('Sketch', modelCount)
          entity = Sketch(key=new_key,
                        sketchId=long(jsonData['sketchId']),
                        version=long(jsonData['version']),
                        changeDescription=change,
                        fileName=jsonData['fileName'],
                        owner=long(jsonData['owner_id']),
                        fileData=file,
                        thumbnailData=thumbnail,
                        original_sketch=long(jsonData['originalSketch']),
                        original_version=long(jsonData['originalVersion']),
                        appver=float(jsonData['appver']),
                        lowerFileName=jsonData['fileName'].lower())
        else:
          entity = Sketch(sketchId=long(jsonData['sketchId']),
                        version=long(jsonData['version']),
                        changeDescription=change,
                        fileName=jsonData['fileName'],
                        owner=long(jsonData['owner_id']),
                        fileData=file,
                        thumbnailData=thumbnail,
                        original_sketch=long(jsonData['originalSketch']),
                        original_version=long(jsonData['originalVersion']),
                        appver=float(jsonData['appver']),
                        lowerFileName=jsonData['fileName'].lower())
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
            if "group_permissions" in jsonData and jsonData['group_permissions']:
              group_permissions = jsonData['group_permissions']
              group_count = Sketch_Groups.add(long(jsonData['sketchId']),
                                              group_permissions)
            #except:
             # group_count = 0
          
            if (permissions_key != -1):
                if 'uniqueId' in jsonData:
                  result = {'id': entity.key().id(),
                            'status': "success",
                            'method': "add",
                            'en_type': "Sketch",
                            'sketchId':long(jsonData['sketchId']),
                            'uniqueId':jsonData['uniqueId'],
                            'data': jsonData}
                else:
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
           if 'uniqueId' in jsonData:
                  result = {'id': entity.key().id(),
                            'status': "success",
                            'method': "add",
                            'en_type': "Sketch",
                            'sketchId':long(jsonData['sketchId']),
                            'uniqueId':jsonData['uniqueId'],
                            'data': jsonData}
           else:
                  result = {'id': entity.key().id(),
                            'status': "success",
                            'method': "add",
                            'en_type': "Sketch",
                            'data': jsonData}      #If sketch was NOT created from latest version
      else:
        result = {'status': "errorDiscrepancy",
                  'message': "This sketch was recently updated to Version " + str(versionCount) + " at " +  thelatestobject_created.strftime("%Y-%m-%d %H:%M") + ". You are trying to save from an older version.",
                  'submessage': " Would you like to overwrite the latest version?",
                  'version': long(versionCount - 1)} 
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
    sketch_id_users = set()
    sketch_id_query = Sketch.all().filter('owner IN',possible_users[:29]).fetch(limit=None)
    if sketch_id_query:
        for obj in sketch_id_query:
            sketch_id_users.add(obj.sketchId)
    union = sketch_id_users | set(possible_names)
    in_clause = list(union)
    count = 0
    remaining = len(in_clause)
    #The IN filter can have maximum of 30 entries
    MAX_COUNT_IN_CLAUSE = 30

    while remaining > 0:
        if remaining < MAX_COUNT_IN_CLAUSE:
            objects = objects+Sketch.all().filter('sketchId IN', in_clause[count:count+remaining]).order('-modified').fetch(limit=None)
            remaining = 0
            count += remaining
        else:
            next = count + MAX_COUNT_IN_CLAUSE
            objects = objects+Sketch.all().filter('sketchId IN', in_clause[count:next]).order('-modified').fetch(limit=None)
            remaining -= MAX_COUNT_IN_CLAUSE
            count += MAX_COUNT_IN_CLAUSE

    entities = []
    count = 0
    next_offset = 0
    
    if objects:
      for object in objects[offset:]:
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
        
        if latest_check and bool(permissions['p_view']):
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
          
        #if count >= limit:
        #  next = objects.index(object) + 1
        #  if next < len(objects):
        #    next_offset = objects.index(object) + 1
        #  break
        
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

    #if model:
      #theQuery = theQuery.filter('model', model)
    
    jsonData = json.loads(data)
    criteria = long(jsonData['id'])
    show = jsonData['show']
    limit = long(jsonData['limit'])
    offset = long(jsonData['offset'])
    sortby = jsonData['sort']
    theQuery = Sketch.all().filter('owner',long(criteria)).filter('isLatest',True).order(sortby)
    count = theQuery.count(limit=None)
    objects = theQuery.fetch(limit=limit, offset=offset)

    entities = []
    next_offset = offset + limit

    for object in objects:
      #Check Permissions
      permissions = Permissions.user_access_control(object.sketchId,userid)
      user_name = User.get_name(object.owner)
      p_view = 0
      p_edit = False
      p_comment = False

      if bool(permissions['p_view']):
        p_view = 1
        p_edit = True
        p_comment = True

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
            'p_edit': p_edit,
            'p_comment': p_comment,
            'like': Like.get_entities_by_id(object.sketchId, 0)['count'],
            'comment': Comment.get_entities_by_id(object.sketchId)['count']}

      entity = {'id': object.key().id(),
            'created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
            'modified': object.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
            'data': data}
      entities.append(entity)
    result = {'method':'get_entities_by_id',
              'en_type': 'Sketch',
              'count': count,
              'offset': offset,
              'limit': limit,
              'next_offset': next_offset,
              'entities': entities}
    return result
  #Test method by Ram for loading without thumbnails
  @staticmethod
  def get_entities_lite(criteria=""):
    utc = UTC()
    #update ModelCount when adding
    param = dict(parse_qsl(criteria))

    theResults = Sketch.all().filter('owner',long(param.get('user'))).order('-created').fetch(limit=None)

    show = "latest"

    entities = []

    userid = long(param.get('user'))

    for object in theResults:
      #if userid == object.owner:
        test = "works!"
        #Latest Version Filter
        latest_check = True
        if show == "latest":
          versionCount = VersionCount.get_counter(long(object.sketchId))
          if object.version < versionCount.lastVersion:
            latest_check = False

        #Check Permissions
        permissions = Permissions.user_access_control(object.sketchId,userid)

        if bool(permissions['p_view']) and latest_check:
          test = "works too!"
          user_name = User.get_name(Crypto.decrypt(object.owner))
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

          if userid == object.owner:
            entities.append(entity)
          elif User.check_if_admin(userid):
            entities.append(entity)
          elif data['p_view'] == "Public":
            entities.append(entity)
    data = []
    offset = int(param.get('offset'))
    count = int(param.get('count'))
    if len(entities) > offset:
        if len(entities) > offset+count:
            data = entities[offset:offset+count]
        else:
            data = entities[offset:]
    modelCount = ModelCount.all().filter('en_type','Sketch').get()
    if modelCount:
      count = modelCount.count
    result = {'count': len(data),
              'entities': data}

    return result
  @staticmethod
  def get_thumbnail(criteria=""):
    #update ModelCount when adding
    theResults = Sketch.all().filter('sketchId',long(criteria)).fetch(limit=None)
    data=""
    if theResults:
        data = theResults[0].thumbnailData
    return data
  #Test method by Cam NEW
  @staticmethod
  def get_entities_by_criteria(criteria=""):
    utc = UTC()
    #update ModelCount when adding
    theResults = Sketch.all().filter('owner',long(criteria)).order('lowerFileName').fetch(limit=None)

    show = "latest"

    entities = []
    
    userid = long(criteria) 

    test = "hello " + criteria

    for object in theResults:
      #if userid == object.owner:
        test = "works!"
        #Latest Version Filter
        latest_check = True
        if show == "latest":
          versionCount = VersionCount.get_counter(long(object.sketchId))
          if object.version < versionCount.lastVersion:
            latest_check = False

        #Check Permissions
        permissions = Permissions.user_access_control(object.sketchId,userid)
          
        if bool(permissions['p_view']) and latest_check:
          test = "works too!"
          user_name = User.get_name(Crypto.decrypt(object.owner))
          data = {'sketchId': object.sketchId,
                'version': object.version,
                'changeDescription': object.changeDescription,
                'fileName': object.fileName,
                'thumbnailData': object.thumbnailData,
                'owner': Crypto.decrypt(user_name),
                'owner_id': object.owner,
                'originalSketch': object.original_sketch,
                'originalVersion': object.original_version,
                'originalName': Sketch.get_sketch_name(object.original_sketch,object.original_version),
                'appver': object.appver,
                'p_view': 1,
                'p_edit': bool(permissions['p_edit']),
                'p_comment': bool(permissions['p_comment']),
                'like': Like.get_entities_by_id(object.sketchId, 0)['count'],
                'comment': Comment.get_entities_by_id(object.sketchId)['count'],
                'lowerFileName': object.lowerFileName}
          
          entity = {'id': object.key().id(),
                'created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'modified': object.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"), 
                'data': data}
          
          if userid == object.owner:
            entities.append(entity)
          elif User.check_if_admin(userid):
            entities.append(entity)
          elif data['p_view'] == "Public":
            entities.append(entity)
    
    count = 0
    modelCount = ModelCount.all().filter('en_type','Sketch').get()
    if modelCount:
      count = modelCount.count
    result = {'method': test, #'get_entities_by_criteria_new',
              'en_type': 'Sketch',
              'count': count,
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

  #Gets a specific Sketch by SketchID and version
  @staticmethod
  def get_entity_by_versioning_mobile(sketchId="", version="", purpose="View", userid=""):
    utc = UTC()
    versionmatch = True
    latestversion = True
    result = {'method':'get_entity_by_versioning_mobile',
              'success':"no",
              'id': 0,
              'created': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
              'modified': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
              'data': ""
              }
    
    try:
      query = Sketch.all()
      query.filter('sketchId =', long(sketchId))
      
      data = query.get()
      
      #jsonData = json.loads(data)
      #sketchId = jsonData['id']
      #version = data.version #jsonData['version']
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
              
          result = {'method':'get_entity_by_versioning_mobile',
                    'en_type': 'Sketch',
                    'status':'success',
                    'id': theobject.key().id(),
                    'created': theobject.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                    'modified': theobject.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"), 
                    'data': data
                    }

        else:
          result = {'method':'get_entity_by_versioning_mobile',
                   'status':"Forbidden"}
      else:
        result = {'method':'get_entity_by_versioning_mobile',
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
    theQuery = Sketch.all().filter("isLatest" , True)
    objects = theQuery.run()
    criteria_lowercase = criteria.lower()
    entities = [x.sketchId for x in objects if criteria_lowercase in x.lowerFileName]
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

  #Deletes a Sketch from mobile version
  @staticmethod
  def delete_mobile(sketch_id, userid):
    can_delete = False
    is_admin = User.check_if_admin(userid)
    is_owner = Sketch.check_if_owner(long(sketch_id), userid)
    is_deleted = True

    if is_owner:
      can_delete = True
    elif is_admin:
      can_delete = True
    if can_delete:
        entities = Sketch.all().filter('sketchId',int(sketch_id)).fetch(limit=None)
        for entity in entities:
          is_deleted = Trash.move_to_trash(entity)
          logging.info("Delete: Sketch " + str(sketch_id) + " has been deleted")
          if is_deleted:
              break
        if is_deleted:
            result = {'status':'success',
            'message': 'Deleted user sketch'}
        else:
            result = {'status':'failure',
            'message': 'Cannot move the sketch to Trash'}
    else:
        result  = {'status':'failure',
            'message': 'You don\'t have permissions to delete the sketch'}
    return result

    #Deletes a Sketch from mobile version
  @staticmethod
  def delete_sketch_permenently(sketch_id, userid):
    can_delete = False
    is_admin = User.check_if_admin(userid)
    is_owner = Trash.check_if_owner(long(sketch_id), userid)
    is_deleted = True

    if is_owner:
      can_delete = True
    elif is_admin:
      can_delete = True
    if can_delete:
        entities = Trash.all().filter('sketchId',int(sketch_id)).fetch(limit=None)
        for entity in entities:
          is_deleted = Trash.delete_permenantly(entity)
          logging.info("Delete: Sketch " + str(sketch_id) + " has been deleted")
          if is_deleted:
              break
        if is_deleted:
            result = {'status':'success',
            'message': 'Deleted user sketch'}
        else:
            result = {'status':'failure',
            'message': 'Cannot move the sketch to Trash'}
    else:
        result  = {'status':'failure',
            'message': 'You don\'t have permissions to delete the sketch'}
    return result

  @staticmethod
  def restore_sketch(sketch_id, userid):
    can_delete = False
    is_admin = User.check_if_admin(userid)
    is_owner = Trash.check_if_owner(long(sketch_id), userid)
    is_deleted = True

    if is_owner:
      can_delete = True
    elif is_admin:
      can_delete = True
    if can_delete:
        entities = Trash.all().filter('sketchId',int(sketch_id)).fetch(limit=None)
        for entity in entities:
          is_deleted = Trash.restore_sketch(entity)
          logging.info("Moved: Sketch " + str(sketch_id) + " has been restored")
          if is_deleted:
              break
        if is_deleted:
            result = {'status':'success',
            'message': 'Restored user sketch'}
        else:
            result = {'status':'failure',
            'message': 'Cannot restore the sketch'}
    else:
        result  = {'status':'failure',
            'message': 'You don\'t have permissions to restore the sketch'}
    return result

  #Deletes a User's data
  @staticmethod
  def delete_sketch_by_user(data):
    jsonData = json.loads(data)
    criteria = long(jsonData['id'])
    
    utc = UTC()
    #update ModelCount when adding
    theQuery = Sketch.all()
    objects = theQuery.run()

    result = {'status':'success',
              'message': 'No sketches to delete'}

    for object in objects:
      if long(criteria) == object.owner:
        sketch_id = object.sketchId
        appver = object.appver

        object.delete()
        ModelCount.decrement_counter('Sketch_count')
        AppVersionCount.decrement_counter(appver, True)
        Comment.delete_by_sketch(long(sketch_id))
        Permissions.delete_by_sketch(long(sketch_id))
        Sketch_Groups.delete_by_sketch(long(sketch_id))
        Like.delete_by_sketch(long(sketch_id))

        result = {'status':'success',
                  'message': 'Deleted user sketches'}

        logging.info("Delete: Sketch " + str(sketch_id) + " has been deleted")

    logging.info("Delete: All sketches of user (" + str(criteria) + ") successfully deleted")

    return result

  @staticmethod
  def get_latest_by_criteria(data=""):
    utc = UTC()
    logging.info(data)
    jsonData = json.loads(data)

    userid = jsonData['userid']
    theResults = Sketch.all().filter('owner',long(userid)).filter('isLatest',True).order('lowerFileName').fetch(limit=None)
    entities = []

    for object in theResults:
          user_name = User.get_name(object.owner)
          if object.sketchId == object.original_sketch:
              data = {'sketchId': object.sketchId,
                    'version': object.version,
                    'changeDescription': object.changeDescription,
                    'fileName': object.fileName,
                    'thumbnailData': object.thumbnailData,
                    'owner': user_name,
                    'owner_id': object.owner,
                    'originalSketch': object.original_sketch,
                    'originalVersion': object.original_version,
                    'originalName': object.fileName,
                    'appver': object.appver,
                    'p_view': 1,
                    'p_edit': True,
                    'p_comment': True,
                    'like': 0,
                    'comment': 0,
                    'lowerFileName': object.lowerFileName}
          else:
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
                    'p_edit': True,
                    'p_comment': True,
                    'like': 0,
                    'comment': 0,
                    'lowerFileName': object.lowerFileName}

          entity = {'id': object.key().id(),
                'created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'modified': object.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'data': data}

          entities.append(entity)
    count = 0
    modelCount = ModelCount.all().filter('en_type','Sketch').get()
    if modelCount:
      count = modelCount.count
    result = {'method': 'get_entities_by_criteria',
              'en_type': 'Sketch',
              'count': count,
              'entities': entities}

    return result
  #Test method by Ram
  @staticmethod
  def get_filenames(criteria=30):
    utc = UTC()
    #update ModelCount when adding
    theResults = Sketch.all().fetch(limit=int(criteria))
    results = []
    for object in theResults:
        result = {"ID":object.sketchId,"FILENAME":object.fileName,"USERID":object.owner}
        results.append(result)
    return results

  #method for mobile v2
  #Test method not used now
  @staticmethod
  def get_entities_v2(criteria=""):
    utc = UTC()
    theResults = Sketch.all().filter('owner',long(criteria)).filter('isLatest',True).order('created').fetch(limit=None)
    entities = []
    for object in theResults:
        user_name = User.get_name(object.owner)
        entity = {'id': object.key().id(),
                'created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'modified': object.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'sketchId': object.sketchId,
                'version': object.version,
                'changeDescription': object.changeDescription,
                'fileName': object.fileName,
                'thumbnailData': object.thumbnailData,
                'owner': user_name,
                'owner_id': object.owner,
                'originalSketch': object.original_sketch,
                'originalVersion': object.original_version}
        entities.append(entity)
    return entities
  @staticmethod
  def update_latest_flag(sketchId):
        to_put = []
        query = Sketch.all().filter('sketchId =', long(sketchId)).fetch(limit=None)
        for p in query:
            p.isLatest = False
            to_put.append(p)
        if to_put:
            db.put(to_put)
  @staticmethod
  def get_entity_by_versioning_mobile_v2(sketchId="", version="", purpose="View", userid=""):
        utc = UTC()
        versionmatch = True
        latestversion = True
        result = {'method':'get_entity_by_versioning_mobile',
                  'success':"no",
                  'id': 0,
                  'created': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                  'modified': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                  'data': ""
                  }

        try:
          query = Sketch.all()
          query.filter('sketchId =', long(sketchId))

          data = query.get()

          #jsonData = json.loads(data)
          #sketchId = jsonData['id']
          #version = data.version #jsonData['version']
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
              result = {'sketchId': theobject.sketchId,
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
                      'islatest': latestversion,
                      'en_type': 'Sketch',
                      'status':'success',
                      'id': theobject.key().id(),
                      'created': theobject.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                      'modified': theobject.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S")}
            else:
              result = {'method':'get_entity_by_versioning_mobile',
                       'status':"Forbidden"}
          else:
            result = {'method':'get_entity_by_versioning_mobile',
                      'status':"Error"}
        except (RuntimeError, ValueError):
          result['data'] = ""

        return result
  @staticmethod
  def get_file_data(sketchId="", version="", purpose="View", userid=""):
    utc = UTC()
    versionmatch = True
    latestversion = True
    result = {'method':'get_entity_by_versioning_mobile',
              'success':"no",
              'id': 0,
              'created': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
              'modified': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
              'data': ""
              }

    try:
      query = Sketch.all()
      query.filter('sketchId =', long(sketchId))

      data = query.get()

      #jsonData = json.loads(data)
      #sketchId = jsonData['id']
      #version = data.version #jsonData['version']
      theobject = None

      versionCount = VersionCount.get_counter(long(sketchId))

      #Get latest version
      if versionCount and long(version) == -1:
        theobject = Sketch.all().filter('sketchId =', long(sketchId)).filter('isLatest =', True).get()
        if theobject == None:
            theobject = Sketch.all().filter('sketchId =', long(sketchId)).get()
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

        #if access:
        result = theobject.fileData

        #else:
        #  result = {'method':'get_entity_by_versioning_mobile',
        #           'status':"Forbidden"}
      else:
        result = {'method':'get_entity_by_versioning_mobile',
                  'status':"Error"}
    except (RuntimeError, ValueError):
      result['data'] = ""

    return result
  #Creates a new Sketch entity from solving discrepancy
  @staticmethod
  def modify_sketch_data(data):
    result = {"success":'false'}
    jsonData = json.loads(data)
    versionCount = VersionCount.get_counter(long(jsonData['id']))
    logging.info(versionCount.lastVersion)
    is_admin = User.check_if_admin(long(jsonData['user_id']))
    if is_admin:
        my_object = Sketch.all().filter("sketchId =",long(jsonData['id'])).filter('version =',versionCount.lastVersion).get()
        my_object.fileData = jsonData['fileData']
        db.put(my_object)
        result['success']='true'
    return result

  @staticmethod
  def get_xml_by_versioning_mobile(sketchId="", version="", purpose="View", userid=""):
    utc = UTC()
    versionmatch = True
    latestversion = True
    result = {'method':'get_xml_by_versioning_mobile',
              'status':"Error",
              'id': 0,
              'created': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
              'modified': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
              'data': ""
              }

    try:
      query = Sketch.all()
      query.filter('sketchId =', long(sketchId))

      data = query.get()

      #jsonData = json.loads(data)
      #sketchId = jsonData['id']
      #version = data.version #jsonData['version']
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
        is_admin = User.check_if_admin(userid)
        if is_admin:
          user_name = User.get_name(theobject.owner)
          data = {'sketchId': theobject.sketchId,
                  'version': theobject.version,
                  'changeDescription': theobject.changeDescription,
                  'fileName': theobject.fileName,
                  'owner': user_name,
                  'owner_id': theobject.owner,
                  'fileData': theobject.fileData}

          result = {'method':'get_entity_by_versioning_mobile',
                    'en_type': 'Sketch',
                    'status':'success',
                    'id': theobject.key().id(),
                    'created': theobject.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                    'modified': theobject.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                    'data': data
                    }

        else:
          result = {'method':'get_xml_by_versioning_mobile',
                   'status':"Forbidden"}
      else:
        result = {'method':'get_xml_by_versioning_mobile',
                  'status':"Error"}
    except (RuntimeError, ValueError):
      result['data'] = ""

    return result
def UpdateSchema(cursor=None, num_updated=0):
    query = Sketch.all()
    if cursor:
        query.with_cursor(cursor)

    to_put = []
    for p in query.fetch(limit=50):
        # In this example, the default values of 0 for num_votes and avg_rating
        # are acceptable, so we don't need this loop.  If we wanted to manually
        # manipulate property values, it might go something like this:

        versionCount = VersionCount.get_counter(long(p.sketchId))
        if p.version < versionCount.lastVersion:
            p.isLatest = False
        else:
            p.isLatest = True
        to_put.append(p)
    if to_put:
        db.put(to_put)
        num_updated += len(to_put)
        logging.debug(
            'Put %d entities to Datastore for a total of %d',
            len(to_put), num_updated)
        deferred.defer(UpdateSchema, cursor=query.cursor(), num_updated=num_updated)
    else:
        logging.debug(
            'UpdateSchema complete with %d updates!', num_updated)

def UpdateLowerFilenames(cursor=None, num_updated=0):
    query = Sketch.all()
    if cursor:
        query.with_cursor(cursor)

    to_put = []
    for p in query.fetch(limit=50):
        # In this example, the default values of 0 for num_votes and avg_rating
        # are acceptable, so we don't need this loop.  If we wanted to manually
        # manipulate property values, it might go something like this:
        p.lowerFileName = p.fileName.lower()
        to_put.append(p)
    if to_put:
        db.put(to_put)
        num_updated += len(to_put)
        logging.info(
            'Put %d entities to Datastore for a total of %d',
            len(to_put), num_updated)
        deferred.defer(UpdateLowerFilenames, cursor=query.cursor(), num_updated=num_updated)
    else:
        logging.info(
            'UpdateSchema complete with %d updates!', num_updated)

#Imports placed below to avoid circular imports
from rpx import User, UTC
from counters import ModelCount, VersionCount, AppVersionCount
from comments_likes import Comment, Like
from permissions_groups import Permissions, Sketch_Groups
from notifications import Notification    
from trash import Trash
from crypto import Crypto