"""Backend Module

@created: Goh Kian Wei (Brandon)
@code_adapted_from: Chris Boesch, Daniel Tsou
"""
"""
Note to self: json.loads = json string to objects. json.dumps is object to json string.
"""
import datetime
import logging
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

class Sketch(db.Model):
  #Use backend record id as the model id for simplicity
  sketchId = db.IntegerProperty(required=True)
  version = db.IntegerProperty(required=True)
  changeDescription = db.StringProperty()
  fileName = db.StringProperty(required=True)
  owner = db.IntegerProperty(required=True)
  fileData = db.TextProperty(required=True)
  thumbnailData = db.TextProperty()
  original = db.StringProperty(required=True) #might be changed
  created = db.DateTimeProperty(auto_now_add=True) #The time that the model was created    
  modified = db.DateTimeProperty(auto_now=True)
  appver = db.FloatProperty()
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d

      
  @staticmethod
  def add(data):
    result = {}
    try:
      #update ModelCount when adding
      jsonData = json.loads(data)
      modelCount = ModelCount.all().filter('en_type','Sketch').get()
      
      #For sketch files saved through "Save As"
      if jsonData['sketchId'] == '':
        if modelCount:
          modelCount.count += 1
          modelCount.put()
        else:
          modelCount = ModelCount(en_type='Sketch', count=1)
          modelCount.put()
        jsonData['sketchId'] = str(modelCount.count)
      #For sketch files saved through "Save As" that were not derived from another file - this might be changed. 
      if (jsonData['original'] == ':') or (jsonData['original'] == ':-1'):
        jsonData['original'] = 'original'
      
      #update VersionCount when adding  
      versionCount = VersionCount.all().filter('sketchId', long(jsonData['sketchId'])).get()
      if versionCount:
        versionCount.lastVersion += 1
        versionCount.put()
      else:
        versionCount = VersionCount(sketchId=long(jsonData['sketchId']), lastVersion=1)
        versionCount.put()
        
      #update AppVersionCount when adding
      appVersionCount = AppVersionCount.all().filter('app_version', float(jsonData['appver'])).get()
      if appVersionCount:
        appVersionCount.sketch_count += 1
        if jsonData['original'] == 'original':
          appVersionCount.original_count += 1
        appVersionCount.put()
      else:
        if jsonData['original'] == 'original':
          appVersionCount = AppVersionCount(app_version=float(jsonData['appver']), sketch_count = 1, original_count = 1)
        else:
          appVersionCount = AppVersionCount(app_version=float(jsonData['appver']), sketch_count = 1, original_count = 0)
        appVersionCount.put()
      
      jsonData['version'] = str(versionCount.lastVersion)
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
                      original=jsonData['original'],
                      appver=float(jsonData['appver']))
      
      verify = entity.put()
      
      if (verify):
      
        #Update permissions when adding
        permissions = Permissions(sketch_id = entity.key().id(),
                                     view = jsonData['p_view'],
                                     edit = jsonData['p_edit'],
                                     comment = jsonData['p_comment'])
        permissions.put()
        #Placeholder for group permissions.
        
        result = {'id': entity.key().id(), 
                  'status': "success",
                  'data': jsonData} #this would also check if the json submitted was valid
      else:
        result = {'status': "error",
                  'message': "Save unsuccessful. Please try again."}
    except:
      result = {'status': "error",
                'message': "Save unsuccessful. Please try again."}
    
    return result
  
  @staticmethod
  def get_entities(criteria="", userid=""):
    utc = UTC()
    #update ModelCount when adding
    theQuery = Sketch.all()
    #if model:
      #theQuery = theQuery.filter('model', model)

    objects = theQuery.run()

    entities = []
    possible_users = User.get_matching_ids(criteria)
    for object in objects:
      include = True
      if criteria != "":
        include = False
        if criteria.lower() in object.fileName.lower():
          include = True
        if object.owner in possible_users:
          include = True
        
      if include:
        user_name = User.get_name(object.owner)
        data = {'sketchId': object.sketchId,
              'version': object.version,
              'changeDescription': object.changeDescription,
              'fileName': object.fileName,
              'thumbnailData': object.thumbnailData,
              'owner': user_name,
              'owner_id': object.owner,
              'original': object.original,
              'appver': object.appver,
              'p_view': "Public",
              'p_view_groups': [],
              'p_edit': "Public",
              'p_edit_groups': [],
              'p_comment': "Public",
              'p_comment_groups': []}
              
        #Retrieves permissions data if applicable:
        permissions = Permissions.all().filter('sketch_id', object.key().id()).get()
        if permissions:
          data['p_view'] = permissions.view
          data['p_edit'] = permissions.edit
          data['p_comment'] = permissions.comment
          #Placeholder for permissions groups
          
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
        #elif data['p_view'] == "Group":
          #Reserved for group permissions  
    
    count = 0
    modelCount = ModelCount.all().filter('en_type','Sketch').get()
    if modelCount:
      count = modelCount.count
    result = {'method':'get_entities',
              'en_type': 'Sketch',
              'count': count,
              'entities': entities}
    return result

  @staticmethod
  def get_entities_by_id(criteria="",userid=""):
    utc = UTC()
    #update ModelCount when adding
    theQuery = Sketch.all()
    #if model:
      #theQuery = theQuery.filter('model', model)

    objects = theQuery.run()

    entities = []
    for object in objects:
      if long(criteria) == object.owner:
        data = {'sketchId': object.sketchId,
              'version': object.version,
              'changeDescription': object.changeDescription,
              'fileName': object.fileName,
              'thumbnailData': object.thumbnailData,
              'owner': object.owner,
              'original': object.original,
              'appver': object.appver,
              'p_view': "Public",
              'p_view_groups': [],
              'p_edit': "Public",
              'p_edit_groups': [],
              'p_comment': "Public",
              'p_comment_groups': []}
              
        #Retrieves permissions data if applicable:
        permissions = Permissions.all().filter('sketch_id', object.key().id()).get()
        if permissions:
          data['p_view'] = permissions.view
          data['p_edit'] = permissions.edit
          data['p_comment'] = permissions.comment
          #Placeholder for permissions groups
          
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
        #elif data['p_view'] == "Group":
          #Reserved for group permissions          
          
    count = 0
    modelCount = ModelCount.all().filter('en_type','Sketch').get()
    if modelCount:
      count = modelCount.count
    result = {'method':'get_entities_by_id',
              'en_type': 'Sketch',
              'count': count,
              'entities': entities}
    return result
    
  @staticmethod
  def get_entity(model_id):
    utc = UTC()
    theobject = Sketch.get_by_id(long(model_id))
    
    user_name = User.get_name(theobject.owner)
    data = {'sketchId': theobject.sketchId,
              'version': theobject.version,
              'changeDescription': theobject.changeDescription,
              'fileName': theobject.fileName,
              'owner': user_name,
              'owner_id': theobject.owner,
              'fileData': theobject.fileData,
              'thumbnailData': theobject.thumbnailData,
              'original': theobject.original,
              'appver': theobject.appver,
              'p_view': "Public",
              'p_view_groups': [],
              'p_edit': "Public",
              'p_edit_groups': [],
              'p_comment': "Public",
              'p_comment_groups': []}
              
    #Retrieves permissions data if applicable:
    permissions = Permissions.all().filter('sketch_id', theobject.key().id()).get()
    if permissions:
      data['p_view'] = permissions.view
      data['p_edit'] = permissions.edit
      data['p_comment'] = permissions.comment
      #Placeholder for permissions groups
    
    result = {'method':'get_model',
              'message':'You have not been granted permission for this sketch.'}
    p_result = {'method':'get_model',
                  'id': model_id,
                  'created': theobject.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                  'modified': theobject.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"), 
                  'data': data
                  }

    if userid == theobject.owner:
      result = p_result
    elif User.check_if_admin(userid):
      result = p_result
    elif data['p_view'] == "Public":
      result = p_result
    #elif data['p_view'] == "Group":
      #Reserved for group permissions                    
    return result

  @staticmethod
  def get_entity_by_versioning(sketchId=-1,version=-1,userid=""):
    utc = UTC()
    versionmatch = True
    result = {'method':'get_entity_by_versioning',
                  'success':"no",
                  'id': 0,
                  'created': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                  'modified': datetime.datetime.now().replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                  'data': ""
                  }
    
    try:
      query = Sketch.all()
      query.filter('sketchId =', long(sketchId)).filter('version =', long(version))
      
      theobject = query.get()
      
      if theobject is None:
        versionCount = VersionCount.all().filter('sketchId', long(sketchId)).get()
        if long(version) != -1:
          versionmatch = False
        
        if versionCount:
          query = Sketch.all()
          query.filter('sketchId =', long(sketchId)).filter('version =', long(versionCount.lastVersion))
          theobject = query.get()
        else:
          result['data'] = "durr"
      
      if theobject:
      
        user_name = User.get_name(theobject.owner)
        data = {'sketchId': theobject.sketchId,
                  'version': theobject.version,
                  'changeDescription': theobject.changeDescription,
                  'fileName': theobject.fileName,
                  'owner': user_name,
                  'owner_id': theobject.owner,
                  'fileData': theobject.fileData,
                  'thumbnailData': theobject.thumbnailData,
                  'original': theobject.original,
                  'appver': theobject.appver,
                  'p_view': "Public",
                  'p_view_groups': [],
                  'p_edit': "Public",
                  'p_edit_groups': [],
                  'p_comment': "Public",
                  'p_comment_groups': []}
              
        #Retrieves permissions data if applicable:
        permissions = Permissions.all().filter('sketch_id', theobject.key().id()).get()
        if permissions:
          data['p_view'] = permissions.view
          data['p_edit'] = permissions.edit
          data['p_comment'] = permissions.comment
          #Placeholder for permissions groups
        
        p_result = {'method':'get_entity_by_versioning',
                      'success':"yes",
                      'id': theobject.key().id(),
                      'created': theobject.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                      'modified': theobject.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"), 
                      'data': data
                      }
        if not versionmatch:
          p_result['success'] = "version"
          
        
        if userid == theobject.owner:
          result = p_result
        elif User.check_if_admin(userid):
          result = p_result
        elif data['p_view'] == "Public":
          result = p_result
        #elif data['p_view'] == "Group":
          #Reserved for group permissions
        else:
          result = {'method':'get_entity_by_versioning',
                        'success':"no",
                        'id': "Forbidden"
                        }
    except (RuntimeError, ValueError):
      result['data'] = "value"
      
    return result
  

    
  @staticmethod
  def clear():
    #update model count when clearing model on api
    count = 0
    for object in Sketch.all():
      count += 1
      object.delete()
      
    modelCount = ModelCount.all().filter('en_type','Sketch').get()
    if modelCount:
      modelCount.delete()
    result = {'items_deleted': count}
    return result
  
  #You can't name it delete since db.Model already has a delete method
  @staticmethod
  def remove(model_id):
    #update model count when deleting
    entity = Sketch.get_by_id(long(model_id))
    
    if entity:
        entity.delete()
    
        result = {'method':'delete_model_success',
                  'id': model_id
                  }
    else:
        result = {'method':'delete_model_not_found'}
        
    modelCount = ModelCount.all().filter('en_type','Sketch').get()
    if modelCount:
        modelCount.count -= 1
        modelCount.put()
    
    return result

  #data is a dictionary that must be merged with current json data and stored. 
  @staticmethod
  def edit_entity(model_id, data):
    jsonData = json.loads(data)
    entity = Sketch.get_by_id(long(model_id))
    
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
    if jsonData['original']!='':
      entity.original=jsonData['original']
    if jsonData['appver']!='':
      entity.appver=float(jsonData['appver'])
    entity.put()
    
    result = {'id': entity.key().id(), 
              'data': json.dumps(jsonData) #this would also check if the json submitted was valid
              }
    return result
    
#Quick retrieval for supported models metadata and count stats
class ModelCount(db.Model):
  en_type = db.StringProperty(required=True,default='Default-entype')
  count = db.IntegerProperty(required=True, default=0)
  
class VersionCount(db.Model):
  sketchId = db.IntegerProperty(required=True, default=0)
  lastVersion = db.IntegerProperty(required=True, default=0)
  
class AppVersionCount(db.Model):
  app_version = db.FloatProperty()
  sketch_count = db.IntegerProperty()
  original_count = db.IntegerProperty()
  

  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
       
  
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
              'status':'success',
              'entities': entities,
              'total': total}  
    return result
  
class Comment(db.Model):
  sketch_id = db.IntegerProperty(required=True)
  user_id = db.IntegerProperty(required=True)
  content = db.StringProperty(required=True)
  reply_to_id = db.IntegerProperty()
  created = db.DateTimeProperty(auto_now_add=True) #The time that the model was created
  
class Permissions(db.Model):
  sketch_id = db.IntegerProperty(required=True)
  view = db.StringProperty(required=True)
  edit = db.StringProperty(required=True)
  comment = db.StringProperty(required=True)
  
class Permissions_Groups(db.Model):
  sketch_id = db.IntegerProperty(required=True)
  permission_id = db.IntegerProperty(required=True)
  permission_type = db.StringProperty(required=True)
  permission_group = db.IntegerProperty(required=True)
  
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
  def get_entities(criteria=""):
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
  def get_entity(model_id):
    utc = UTC()
    theobject = Group.get_by_id(long(model_id))
    
    user_groups_query = UserGroupMgmt.all().filter('group_id', theobject.key().id()).run()
    u_groups = []
    
    if user_groups_query:
      for u_g in user_groups_query:
        user_name = User.get_name(u_g.user_id)
        u_entity = {'user': user_name,
              'user_id': u_g.user_id,#placeholder
              'role': u_g.role}
        u_groups.append(u_entity)    
    
    result = {'method':'get_entity',
                  'id': model_id,
                  'group_name': theobject.group_name,
                  'u_groups': u_groups
                  }
    return result    
  
class UserGroupMgmt(db.Model):
  user_id = db.IntegerProperty(required=True)
  group_id = db.IntegerProperty(required=True)
  role = db.StringProperty(required=True)
  
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

    def metadata(self):
        #Fetch all ModelCount records to produce metadata on currently supported models. 
        models = []
        for mc in ModelCount.all():
          models.append({'model':mc.model, 'count': mc.count})
    
        result = {'method':'metadata',
                  'model': "metadata",
                  'count': len(models),
                  'entities': models
                  } 
        
        return self.respond(result)

    def add_or_list_sketch(self): #/sketch
        #Check for GET paramenter == model to see if this is an add or list. 
        #Call Sketch.add(model, data) or
        #Fetch all models and return a list. 
                
        #Todo - Check for method.
        logging.info(self.request.method)
        if self.request.method=="POST":
          logging.info("in POST")
          logging.info(self.request.body)
          result = Sketch.add(self.request.body)
          #logging.info(result)
          return self.respond(result)
    
        else:
          data = self.request.get("obj")
          if data: 
            logging.info("Adding new data: "+data)
            result = Sketch.add(data)
          else:
            offset = 0
            new_offset = self.request.get("offset")
            if new_offset:
              offset = int(new_offset)

            result = Sketch.get_entities(offset=offset)
          
          return self.respond(result)

    def delete_sketch(self, model_id):
        result = Sketch.remove(model_id)
        
        return self.respond(result)
      
    def get_or_edit_sketch(self, model_id):
        #Check for GET parameter == model to see if this is a get or an edit
        logging.info("**********************")
        logging.info(self.request.method)
        logging.info("**********************")

        if self.request.method=="DELETE":
          logging.info("It was options")
          result = Sketch.remove(model_id)
          logging.info(result)
          return self.respond(result)#(result)
        
        elif self.request.method=="PUT":
          logging.info("It was PUT")
          logging.info(self.request.body)
          result = Sketch.edit_entity(model_id,self.request.body)
          return self.respond(result)#(result)          
        else:
          data = self.request.get("obj")
          if data:
              result = Sketch.edit_entity(model_id,data)
          else:
              result = Sketch.get_entity(model_id)
          return self.respond(result) 
          
    def user_sketch(self, criteria): #/list/sketch/user/<criteria>
        #Check for GET parameter == model to see if this is a get or an edit
        logging.info("**********************")
        logging.info(self.request.method)
        logging.info("**********************")

        auser = self.auth.get_user_by_session()
        userid = ""
        if auser:
          userid = auser['user_id']
          
        result = Sketch.get_entities_by_id(criteria=criteria,userid=userid)
        return self.respond(result)    
        
    def search_sketch(self, criteria): #/list/sketch/<criteria>
        #Check for GET parameter == model to see if this is a get or an edit
        logging.info("**********************")
        logging.info(self.request.method)
        logging.info("**********************")

        offset = 0
        new_offset = self.request.get("offset")
        if new_offset:
          offset = int(new_offset)

        auser = self.auth.get_user_by_session()
        userid = ""
        if auser:
          userid = auser['user_id']

        result = Sketch.get_entities(criteria=criteria,userid=userid)
        return self.respond(result)
      
    def list_sketch(self): #/list/sketch
        #Check for GET parameter == model to see if this is a get or an edit
        logging.info("**********************")
        logging.info(self.request.method)
        logging.info("**********************")

        offset = 0
        new_offset = self.request.get("offset")
        if new_offset:
          offset = int(new_offset)

        auser = self.auth.get_user_by_session()
        userid = ""
        if auser:
          userid = auser['user_id']
          
        result = Sketch.get_entities(userid=userid)
        return self.respond(result)
      
    def get_sketch_by_version(self, sketchId, version): #/get/sketch/version/<sketchId>/<version>
        #Check for GET parameter == model to see if this is a get or an edit
        logging.info("**********************")
        logging.info(self.request.method)
        logging.info("**********************")

        auser = self.auth.get_user_by_session()
        userid = ""
        if auser:
          userid = auser['user_id']
        
        result = Sketch.get_entity_by_versioning(sketchId, version, userid=userid)
        return self.respond(result) 
        
    def add_group(self):
        #Check for GET paramenter == model to see if this is an add or list. 
        #Call Sketch.add(model, data) or
        #Fetch all models and return a list. 
                
        #Todo - Check for method.
        logging.info(self.request.method)
        if self.request.method=="POST":
          logging.info("in POST")
          logging.info(self.request.body)
          result = Group.add(self.request.body)
          #logging.info(result)
          return self.respond(result)
    
        else:
          data = self.request.get("obj")
          if data: 
            logging.info("Adding new data: "+data)
            result = Group.add(data)
          return self.respond(result)

    def get_group(self, model_id):
        #Check for GET parameter == model to see if this is a get or an edit
        logging.info("**********************")
        logging.info(self.request.method)
        logging.info("**********************")

        result = Group.get_entity(model_id)
        return self.respond(result) 

    def user_group(self, criteria):
        #Check for GET parameter == model to see if this is a get or an edit
        logging.info("**********************")
        logging.info(self.request.method)
        logging.info("**********************")

        offset = 0
        new_offset = self.request.get("offset")
        if new_offset:
          offset = int(new_offset)

        result = Group.get_entities(criteria=criteria)
        return self.respond(result)
        
    def get_versions(self):
        #Check for GET parameter == model to see if this is a get or an edit
        logging.info("**********************")
        logging.info(self.request.method)
        logging.info("**********************")

        offset = 0
        new_offset = self.request.get("offset")
        if new_offset:
          offset = int(new_offset)

        result = AppVersionCount.retrieve_by_version()
        return self.respond(result)
        
webapp2_config = {}
webapp2_config['webapp2_extras.sessions'] = {
		'secret_key': 'n\xd99\xd4\x01Y\xea5/\xd0\x8e\x1ba\\:\x91\x10\x16\xbcTA\xe0\x87lf\xfb\x0e\xd2\xc4\x15\\\xaf\xb0\x91S\x12_\x86\t\xadZ\xae]\x96\xd0\x11\x80Ds\xd5\x86.\xbb\xd5\xcbb\xac\xc3T\xaf\x9a+\xc5',
	}

application = webapp2.WSGIApplication([
    webapp2.Route('/metadata', handler=ActionHandler, handler_method='metadata'),
    webapp2.Route('/sketch/<model_id>/delete', handler=ActionHandler, handler_method='delete_sketch'), 
    webapp2.Route('/sketch/<model_id>', handler=ActionHandler, handler_method='get_or_edit_sketch'), 
    webapp2.Route('/sketch', handler=ActionHandler, handler_method='add_or_list_sketch'), #
    webapp2.Route('/list/sketch', handler=ActionHandler, handler_method='list_sketch'), #
    webapp2.Route('/list/sketch/<criteria>', handler=ActionHandler, handler_method='search_sketch'), #
    webapp2.Route('/list/sketch/user/<criteria>', handler=ActionHandler, handler_method='user_sketch'), #
    #webapp2.Route('/get/sketch/<model_id>', handler=ActionHandler, handler_method='get_sketch'), #
    webapp2.Route('/get/sketch/version/<sketchId>/<version>', handler=ActionHandler, handler_method='get_sketch_by_version'), #
    webapp2.Route('/group', handler=ActionHandler, handler_method='add_group'), 
    webapp2.Route('/get/group/<model_id>', handler=ActionHandler, handler_method='get_group'),
    webapp2.Route('/list/group/<criteria>', handler=ActionHandler, handler_method='user_group'),
    webapp2.Route('/list/version', handler=ActionHandler, handler_method='get_versions')
    ],
    config=webapp2_config,
    debug=True)
