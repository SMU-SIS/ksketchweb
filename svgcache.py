'''
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
'''

from google.appengine.ext import db
import logging
import json
class SVGCache(db.Model):
    sketchId = db.IntegerProperty(required=True)
    version = db.IntegerProperty(required=True)
    svgData = db.TextProperty(required=False)
    animationData = db.TextProperty(required=False)

    #Creates a new cache entry
    @staticmethod
    def addSVGData(_sketchId, _versionNumber, _svgData):
        handmade_key = db.Key.from_path('Sketch', 1)
        new_ids = db.allocate_ids(handmade_key, 1)
        entity = SVGCache(sketchId=int(_sketchId),version=int(_versionNumber),svgData=_svgData)
        entity.put()


    @staticmethod
    def addAnimationData(_sketchId, _version, _animationData):
        cache = SVGCache.getSVGCache(_sketchId,_version)
        logging.info(cache)
        if cache:
            cache.animationData = json.dumps(_animationData)
            cache.put()

    @staticmethod
    def getSVGCache(_sketchId, _version):
        cache = SVGCache.all().filter('sketchId =',int(_sketchId)).filter('version =',int(_version)).get()
        if cache:
            return cache
        return None
