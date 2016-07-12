'''
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
'''
from google.appengine.ext import db
import json

class DeletedSketch(db.Model):
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
    lowerFileName = db.StringProperty(default="")
    overwrite = False

    def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d

class Trash(db.Model):
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
    lowerFileName = db.StringProperty(default="")
    overwrite = False

    def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d


    @staticmethod
    def move_to_trash(sketch):
        entity = Trash(sketchId = sketch.sketchId,
                       version = sketch.version,
                       changeDescription = sketch.changeDescription,
                       fileName = sketch.fileName,
                       owner = sketch.owner,
                       fileData = sketch.fileData,
                       thumbnailData = sketch.thumbnailData,
                       original_sketch = sketch.original_sketch,
                       original_version = sketch.original_version,
                       created = sketch.created,
                       modified = sketch.modified,
                       appver = sketch.appver,
                       isLatest = sketch.isLatest,
                       lowerFileName = sketch.lowerFileName)
        verify = entity.put()
        if(verify):
            sketch.delete()
            return True
        else:
            return False

    @staticmethod
    def delete_permenantly(sketch):
        entity = DeletedSketch(sketchId = sketch.sketchId,
                       version = sketch.version,
                       changeDescription = sketch.changeDescription,
                       fileName = sketch.fileName,
                       owner = sketch.owner,
                       fileData = sketch.fileData,
                       thumbnailData = sketch.thumbnailData,
                       original_sketch = sketch.original_sketch,
                       original_version = sketch.original_version,
                       created = sketch.created,
                       modified = sketch.modified,
                       appver = sketch.appver,
                       isLatest = sketch.isLatest,
                       lowerFileName = sketch.lowerFileName)
        verify = entity.put()
        if(verify):
            sketch.delete()
            return True
        else:
            return False

    @staticmethod
    def restore_sketch(sketch):
        entity = Sketch(sketchId = sketch.sketchId,
                       version = sketch.version,
                       changeDescription = sketch.changeDescription,
                       fileName = sketch.fileName,
                       owner = sketch.owner,
                       fileData = sketch.fileData,
                       thumbnailData = sketch.thumbnailData,
                       original_sketch = sketch.original_sketch,
                       original_version = sketch.original_version,
                       created = sketch.created,
                       modified = sketch.modified,
                       appver = sketch.appver,
                       isLatest = sketch.isLatest,
                       lowerFileName = sketch.lowerFileName)
        verify = entity.put()
        if(verify):
            sketch.delete()
            return True
        else:
            return False
    @staticmethod
    def get_entities_by_id(data,userid=""):
        utc = UTC()
        jsonData = json.loads(data)
        criteria = long(jsonData['id'])
        sortby = jsonData['sort']
        theQuery = Trash.all().filter('owner',long(criteria)).filter('isLatest',True).order(sortby)
        objects = theQuery.fetch(limit=None)

        entities = []
        for object in objects:
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
                'originalName': object.fileName,
                'appver': object.appver,
                'p_view': 1,
                'p_edit': True,
                'p_comment': True,
                'like': Like.get_entities_by_id(object.sketchId, 0)['count'],
                'comment': Comment.get_entities_by_id(object.sketchId)['count']}

          entity = {'id': object.key().id(),
                'created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'modified': object.modified.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'data': data}
          entities.append(entity)
        result = {'method':'view_trash_sketches',
                  'en_type': 'Trash',
                  'entities': entities}
        return result
    @staticmethod
    def check_if_owner(id = 0, user_id = 0):
        is_owner = False
        try:
          if long(user_id) != 0:
            versionCount = VersionCount.get_counter(id)
            object = Trash.all().filter('sketchId',id).filter('version',long(versionCount.lastVersion)).get()
            if object:
              if object.owner == long(user_id):
                is_owner = True
        except ValueError:
          is_owner = False
        return is_owner

from rpx import UTC, User
from sketches import VersionCount, Sketch
from comments_likes import Comment, Like
from crypto import Crypto