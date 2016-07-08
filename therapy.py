'''
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
'''

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
from google.appengine.ext import db
from crypto import Crypto

#Handles Therapy data: adding and getting of therapy data
class Therapy(db.Model):
    userName = db.StringProperty(default="") #Name of user
    templateName = db.StringProperty(default="") #Name of Therapy template
    resultDate = db.StringProperty(default="") #Date of therapy data is generated
    resultRecall = db.StringProperty(default="") #<template object id>:<trials>:<time given>:<time taken>:<stars>:<retry>
    resultTrace = db.StringProperty(default="") #<template object id>:<trials>:<time given>:<time taken>:<stars>:<retry>
    resultTrack = db.StringProperty(default="") #<template object id>:<trials>:<time given>:<time taken>:<stars>:<retry>
    resultRecreate = db.StringProperty(default="") #<template object id>:<trials>:<time given>:<time taken>:<stars>:<retry>
    created = db.DateTimeProperty(auto_now_add=True) #Date of Therapy data is saved into the datastore
    modified = db.DateTimeProperty(auto_now=True) #Date of Therapy data is updated in the datastore
    version = db.IntegerProperty() #Version of Sketch.

    #Creates a new therapy data entity
    @staticmethod
    def add(userName, templateName, resultDate, resultRecall, resultTrace, resultTrack, resultRecreate):
        result = {}
        try:
            if userName != "":
                #Check if the therapy data is new data
                isNew = True
                object = Therapy.get_therapydata(userName, templateName, resultDate)
                if object['data'] != "":
                    isNew = False

                if isNew:
                    version = 0
                    entity = Therapy(
                                    version=long(version),
                                    userName=Crypto.encrypt(userName),
                                    templateName=templateName,
                                    resultDate=resultDate,
                                    resultRecall=resultRecall,
                                    resultTrace=resultTrace,
                                    resultTrack=resultTrack,
                                    resultRecreate=resultRecreate)
                    entity.put()
                    result={'status': "add successful",
                        'message': "Added new therapy data into Datastore: user name: " + userName + ", template name: " + templateName + ", result date: " + resultDate}
                else:
                    Therapy.update(userName, templateName, resultDate, resultRecall, resultTrace, resultTrack, resultRecreate)
                    result={'status': "update successful",
                        'message': "Updated therapy data for user name: " + userName + ", template name: " + templateName + ", result date: " + resultDate}

            else:
              result = {'status': "error",
                        'message': "Please provide user name."}
        except:
            result = {'status': "error",
                   'message': "Save of Therapy data is unsuccessful. Please try again."}

        return result

    @staticmethod
    def get_entities(self):
        entities = []
        data = {
            'version':"",
            'userName' : "",
            'templateName' : "",
            'resultDate' : "",
            'resultRecall': "",
            'resultTrace': "",
            'resultTrack': "",
            'resultRecreate': ""
        }
        try:
            objects = Therapy.all().order('userName').fetch(limit=None)
            if objects:
                for object in objects:

                    data = {
                        'version': object.version,
                        'userName' : Crypto.decrypt(object.userName),
                        'templateName' : object.templateName,
                        'resultDate' : object.resultDate,
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
    def get_therapydata(userName, templateName, resultDate):
        data = ""
        query = Therapy.all()
        cipher_text = Crypto.encrypt(userName)
        query.filter('userName =',cipher_text).filter('templateName = ',templateName).filter('resultDate',resultDate).fetch(limit=None)
        object = query.get()
        if object:
            data = {
                'userName' : Crypto.decrypt(object.userName),
                'templateName' : object.templateName,
                'resultDate' : object.resultDate,
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
                      'message': "Data is not found.",
                      'data': ""}
        return result

    @staticmethod
    def getData(content):
        datalist = []
        data = {
            'objectTemplateId':"",
            'trials':"",
            'timeGiven':"",
            'timeTaken':"",
            'stars':"",
            'retry':""
        }
        if content!= '':
            if(content.find("|") > 0):
                array = content.split('|')
                for i in range(len(array)):
                    if(array[i] != ''):
                        data = Therapy.getDataItem(array[i])
                        datalist.append(data)
            else:
                data = Therapy.getDataItem(content)
                datalist.append(data)
        return datalist

    @staticmethod
    def getDataItem(content):
        data = {
            'objectTemplateId':"",
            'trials':"",
            'timeGiven':"",
            'timeTaken':"",
            'stars':"",
            'retry':""
        }
        if content!= '':
            array = content.split(':')
            data = {
                'objectTemplateId':array[0],
                'trials':array[1],
                'timeGiven':array[2],
                'timeTaken':array[3],
                'stars':array[4],
                'retry':array[5]
            }
        return data

    @staticmethod
    def update(userName, templateName, resultDate, resultRecall, resultTrace, resultTrack, resultRecreate):
        query = Therapy.all()
        query.filter('userName =',Crypto.encrypt(userName)).filter('templateName = ',templateName).filter('resultDate',resultDate).fetch(limit=None)
        object = query.get()
        if object:
            if object.resultRecall == resultRecall and object.resultTrace == resultTrace and object.resultTrack == resultTrack and object.resultRecreate == resultRecreate:
                return
            else:
                object.version = object.version + 1
                Therapy.add_version(object.version, userName, templateName, resultDate, resultRecall, resultTrace, resultTrack, resultRecreate)

    @staticmethod
    def add_version(version, userName, templateName, resultDate, resultRecall, resultTrace, resultTrack, resultRecreate):
        try:
            entity = Therapy(
                    version=long(version),
                    userName=Crypto.encrypt(userName),
                    templateName=templateName,
                    resultDate=resultDate,
                    resultRecall=resultRecall,
                    resultTrace=resultTrace,
                    resultTrack=resultTrack,
                    resultRecreate=resultRecreate)
            entity.put()
        except:
            result = {'status': "error",
                   'message': "Save of Therapy data is unsuccessful. Please try again."}
