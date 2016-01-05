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
    resultRecall = db.StringProperty(default="")
    resultTrace = db.StringProperty(default="")
    resultTrack = db.StringProperty(default="")
    resultRecreate = db.StringProperty(default="")
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d

    #Creates a new therapy data entity
    @staticmethod
    def add(sketchId, version, result_Recall, result_Trace, result_Track, result_Recreate):
        result = {}
        try:
            if sketchId != "":
                if version == '':
                    version = 0
                #Check if the therapy data is new data
                isNew = True
                object = Therapy.get_therapydata(sketchId)
                if object['data'] != "":
                    isNew = False

                if isNew:
                    version = 0
                    entity = Therapy(sketchId=long(sketchId),
                                    version=long(version),
                                    resultRecall=result_Recall,
                                    resultTrace=result_Trace,
                                    resultTrack=result_Track,
                                    resultRecreate=result_Recreate)
                    entity.put()
                    result={'status': "add successful",
                        'message': "Added new therapy data into Datastore: sketch ID: " + str(sketchId) + ", version: " + str(version)}
                else:
                    Therapy.update_version(sketchId,version,result_Recall,result_Trace,result_Track,result_Recreate)
                    result={'status': "update successful",
                        'message': "Updated therapy data for sketch ID: " + str(sketchId) + " to version: " + str(version)}

            else:
              result = {'status': "error",
                        'message': "Please provide sketch ID."}
        except:
            result = {'status': "error",
                   'message': "Save of Therapy data is unsuccessful. Please try again."}

        return result

    @staticmethod
    def get_entities(self):
        entities = []
        data = {
            'sketchId': "",
            'version':"",
            'resultRecall': "",
            'resultTrace': "",
            'resultTrack': "",
            'resultRecreate': ""
        }
        try:
            objects = Therapy.all().order('sketchId').fetch(limit=None)
            if objects:
                for object in objects:

                    data = {
                        'sketchId': object.sketchId,
                        'version': object.version,
                        'resultRecall': Therapy.getData(object.resultRecall),
                        'resultTrace': Therapy.getData(object.resultTrace),
                        'resultTrack': Therapy.getData(object.resultTrack),
                        'resultRecreate': Therapy.getData(object.resultRecreate)
                    }
                    entities.append(data)
        except:
            result = {'status': "error",
                      'message': "Therapy data is not available"
                      }
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
                'version': object.version,
                'resultRecall': Therapy.getData(object.resultRecall),
                'resultTrace': Therapy.getData(object.resultTrace),
                'resultTrack': Therapy.getData(object.resultTrack),
                'resultRecreate': Therapy.getData(object.resultRecreate)
            }
            result = {'status': "success",
                      'message': "Found therapy data",
                      'data': data}
        else:
            result = {'status': "error",
                      'message': "Sketch ID is not found.",
                      'data': ""}
        return result

    @staticmethod
    def getData(content):
        data = {
            'time':"",
            'accuracy':"",
            'quadrant':"",
            'trials':"",
            'stars':""
        }
        if content!= '':
            array = content.split(':')
            data = {'time':array[0],
                'accuracy':array[1],
                'quadrant':array[2],
                'trials':array[3],
                'stars':array[4]
            }
        return data

    @staticmethod
    def update_version(sketchId,version,result_Recall,result_Trace,result_Track,result_Recreate):
        query = Therapy.all()
        query.filter('sketchId =',long(sketchId)).fetch(limit=None)
        object = query.get()
        if object:
            object.version = long(version)
            object.resultRecall = result_Recall
            object.resultTrace = result_Trace
            object.resultTrack = result_Track
            object.resultRecreate = result_Recreate
            db.put(object)