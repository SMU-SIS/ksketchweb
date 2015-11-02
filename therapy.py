'''
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
'''
import logging
from counters import ModelCount

"""Therapy Data Module

@created: Nguyen Thi Ngoc
@code_adapted_from: Chris Boesch, Daniel Tsou
"""
"""
Note to self: json.loads = json string to objects. json.dumps is object to json string.
"""
"""
Attributes and functions for Therapydata entity
"""
from rpx import UTC
from google.appengine.ext import db

#Handles Therapy data: adding and getting of therapy data
class Therapy(db.Model):
    sketchId = db.IntegerProperty(required=True) #Sketch ID of Sketch.
    version = db.IntegerProperty(required=True) #Version of Sketch.
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d

    #Creates a new therapy data entity
    @staticmethod
    def add(sketchId, version):
        result = {}
        try:
            if sketchId != "":
                if version == '':
                    version = 0
                #Check if the therapy data is new data
                isNew = True
                data = Therapy.get_therapydata(sketchId)
                if data != "":
                    isNew = False

                if isNew:
                    version = 0
                    entity = Therapy(sketchId=long(sketchId),
                                version=long(version))
                    entity.put()
                    result={'status': "add successful",
                        'message': "Added new therapy data into Datastore: sketch ID: " + str(sketchId) + ", version: " + str(version)}
                else:
                    Therapy.update_version(sketchId,version)
                    result={'status': "update successful",
                        'message': "Updated therapy data for sketch ID: " + str(sketchId) + " to version: " + str(version)}

            else:
              result = {'status': "error",
                        'message': "Please provide sketch ID."}
        except:
            result = {'status': "error",
                   'message': "Save Therapy data unsuccessful. Please try again."}

        return result

    @staticmethod
    def get_entities(self):
        entities = []
        data = {
            'sketchId': "",
            'version':""
        }
        objects = Therapy.all().order('sketchId').fetch(limit=None)
        for object in objects:
            data = {
                'sketchId': object.sketchId,
                'version': object.version
            }
            entities.append(data)
        return entities

    @staticmethod
    def get_therapydata(sketchId):
        utc = UTC()
        data = ""
        query = Therapy.all()
        query.filter('sketchId =',long(sketchId)).fetch(limit=None)
        object = query.get()
        if object:
            data = {
                'sketchId': object.sketchId,
                'version': object.version
            }
        else:
            result = {'status': "error",
                    'message': "Sketch ID is not found."}
        return data

    @staticmethod
    def update_version(sketchId,version):
        query = Therapy.all()
        query.filter('sketchId =',long(sketchId)).fetch(limit=None)
        object = query.get()
        if object:
            object.version = long(version)
            db.put(object)