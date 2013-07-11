import datetime
import hashlib
import os
import urllib
import urllib2
import webapp2
import logging

from webapp2_extras import auth
from webapp2_extras import sessions
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

import json

from google.appengine.api import urlfetch
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


# configure the RPX iframe to work with the server were on (dev or real)
ON_LOCALHOST = ('Development' == os.environ['SERVER_SOFTWARE'][:11])
if ON_LOCALHOST:
    import logging
    if os.environ['SERVER_PORT'] == '80':
        BASE_URL = 'localhost'
    else:
        BASE_URL = 'localhost:%s' % os.environ['SERVER_PORT']
else:
    BASE_URL = 'ksketchweb.appspot.com'
LOGIN_IFRAME = '<iframe src="http://gae-sesssions-demo.rpxnow.com/openid/embed?token_url=http%3A%2F%2F' + BASE_URL + '%2Frpx_response" scrolling="no" frameBorder="no" allowtransparency="true" style="width:400px;height:240px"></iframe>'

class UTC(datetime.tzinfo):
  def utcoffset(self, dt):
    return datetime.timedelta(hours=0)
    
  def dst(self, dt):
    return datetime.timedelta(0)
    
  def tzname(self, dt):
    return "UTC"
# create our own simple users model to track our user's data
class User(db.Model):
  email              = db.EmailProperty()
  display_name       = db.StringProperty()
  real_name          = db.StringProperty()
  created            = db.DateTimeProperty(auto_now_add=True)
  modified           = db.DateTimeProperty(auto_now=True)
  lastlogin          = db.DateTimeProperty()
  logincount         = db.IntegerProperty()
  assigned_version   = db.FloatProperty()
  is_admin           = db.BooleanProperty()
  is_active          = db.BooleanProperty()

  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
       
  @staticmethod
  def get_name(model_id):
    #Retrieves display name
    if int(model_id) == 0:
      return "Anonymous User"
    else:
      try:
        entity = User.get_by_id(int(model_id))
        
        if entity:
          return entity.display_name
        else:
          return "N/A"
      except ValueError:
        return "N/A"    
        
  @staticmethod
  def check_if_admin(model_id):
    #Checks admin status
    try:
      if int(model_id) == 0:
        return False
      else:
        entity = User.get_by_id(int(model_id))
        
        if entity:
          return entity.is_admin
        else:
          return False
    except ValueError:
      return False    

  @staticmethod
  def get_matching_ids(criteria=""):
    theQuery = User.all()
    objects = theQuery.run()
    entities = []
    if criteria != "":
      if criteria.lower() in "Anonymous User".lower():
        entities.append(0)
      for object in objects:
        include = True
        if criteria.lower() in object.display_name.lower():
          include = True
        else:
          include = False
        
        if include:
          entities.append(object.key().id())
          
    return entities
        
  @staticmethod
  def search_users_by_name(criteria=""):
    theQuery = User.all()
    objects = theQuery.run()
    entities = []
    if criteria != "":
      if criteria.lower() in "Anonymous User".lower():
        entities.append(0)
      for object in objects:
        include = True
        if criteria.lower() in object.display_name.lower():
          include = True
        else:
          include = False
        
        if include:
          data = {'id': object.key().id(),
                  'u_name': object.display_name,
                  'u_realname': object.real_name}
          entities.append(data)
    else:
      for object in objects:
      
        data = {'id': object.key().id(),
                'u_name': object.display_name,
                'u_realname': object.real_name}
        entities.append(data)  
            
    return entities
    
    @staticmethod
    def get_entities(criteria=""):
      utc=UTC()
      
      theQuery = User.all()
      objects = theQuery.run()
      
      entities = []
      
      for object in objects:
        include = True
        if criteria != "":
          if criteria.lower() in object.display_name.lower():
            include = True
            
        if include:
          email_hasher = hashlib.md5()
          email_hasher.update(user.email.lower())
          g_hash = email_hasher.hexdigest()
          if (not object.real_name):
            object.real_name = object.display_name #default to display name
            object.put()
          data = {'id': object.key().id(),
                      'u_name': object.display_name,
                      'u_realname': object.real_name,
                      'u_email': object.email,
                      'g_hash': g_hash,
                      'u_created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                      'u_lastlogin': "",
                      'u_logincount': object.logincount,
                      'u_version': object.assigned_version,
                      'u_isadmin': object.is_admin,
                      'u_isactive': object.is_active}
          if (object.lastlogin):
            data['u_lastlogin'] = object.lastlogin.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S")
          entities.append(data)
      result = {'method':'get_entities_by_id',
                'en_type':'User',
                'entities':entities}
      return result
                  
  @staticmethod
  def edit_entity(model_id, data):
    jsonData = json.loads(data)
    entity = User.get_by_id(long(model_id))
    result = {'method':'edit_entity',
              'model':'User',
              'success':False}
    if entity:
      if jsonData['u_realname']:
        entity.realname = jsonData['u_realname']
        #Other fields to be added as necessary.
      entity.put()
    
      result = {'method':'edit_entity',
              'model':'User',
              'success':True}
              
    return result
    
class AppUserCount(db.Model):
  app_version = db.FloatProperty()
  user_count = db.IntegerProperty()
  

  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d  
        
    
class BaseHandler(webapp2.RequestHandler):
    """
      BaseHandler for all requests
       Holds the auth and session properties so they are reachable for all requests
    """

    def dispatch(self):
      """
        Save the sessions for preservation across requests
      """
      try:
          response = super(BaseHandler, self).dispatch()
          self.response.write(response)
      finally:
          self.session_store.save_sessions(self.response)

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

    @webapp2.cached_property
    def auth_config(self):
      """
        Dict to hold urls for login/logout
      """
      return {
          'login_url': '/index.html',
          'logout_url': '/index.html'
      }    
    
class RPXTokenHandler(BaseHandler):
    """Receive the POST from RPX with our user's login information."""
    def post(self):
        token = self.request.get('token')
        url = 'https://rpxnow.com/api/v2/auth_info'
        args = {
            'format': 'json',
            'apiKey': '6c8271a5a23692efa86799f3438e3ac7b0525ac0',
            'token': token
        }
        r = urlfetch.fetch(url=url,
                           payload=urllib.urlencode(args),
                           method=urlfetch.POST,
                           headers={'Content-Type':'application/x-www-form-urlencoded'})
        json_data = json.loads(r.content)

        if json_data['stat'] == 'ok':
          # extract some useful fields
          info = json_data['profile']
          oid = info['identifier']
          email = info.get('email', '')
          try:
            display_name = info['displayName']
          except KeyError:
            display_name = email.partition('@')[0]

          # check if there is a user present with that auth_id
          user = self.auth.store.user_model.get_by_auth_id(oid)
          if not user:
            #Version currently hardcoded as 1.0 - to import code for this later.
            appver = 1.0
            
            success, user = self.auth.store.user_model.create_user(oid, email=email, display_name=display_name, real_name=display_name, logincount=0, assigned_version=appver, is_admin=False, is_active=True)
            logging.info('New user created in the DS')
            
            #update AppUserCount when adding
            appUserCount = AppUserCount.all().filter('app_version', appver).get()
            if appUserCount:
              appUserCount.user_count += 1
              appUserCount.put()
            else:
              appUserCount = AppUserCount(app_version=appver,user_count = 1)
              appUserCount.put()   
          
          userid = user.get_id()
          if not user.logincount:
            user.logincount = 1
          else:
            user.logincount += 1 
          user.lastlogin = datetime.datetime.now()
          user.put()
                 
          
          token = self.auth.store.user_model.create_auth_token(userid)
          self.auth.get_user_by_token(userid, token)
          logging.info('The user is already present in the DS')
          
          # assign a session
          self.session.add_flash('You have successfully logged in', 'success')
          self.redirect('/')
        else:
          self.session.add_flash('There was an error while processing the login', 'error')
          self.redirect('/')

class GetUser(webapp2.RequestHandler):
        
    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    """Class which handles bootstrap procedure and seeds the necessary
    entities in the datastore.
    """
        
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
        
    def edit_user(self, **kwargs):
      utc = UTC()
      jsonData = json.loads(self.request.body)
      auser = self.auth.get_user_by_session()
      result = {'method':'edit_entity',
              'model':'User',
              'success':False}
      if auser:
        userid = auser['user_id']
        if userid:
          result = User.get_by_id(userid)
          
      return self.respond(result) 

    
    def get_user(self, **kwargs):
      utc = UTC()
      result = {'status':'error',
                'u_login': bool(False),
                'message':''}
      auser = self.auth.get_user_by_session()
      if auser:
        userid = auser['user_id']
        if userid:
          user = User.get_by_id(userid)
          if user:
            email_hasher = hashlib.md5()
            email_hasher.update(user.email.lower())
            g_hash = email_hasher.hexdigest()
            if (not user.real_name):
              user.real_name = user.display_name #default to display name
              user.put()
            result = {'status':'success',
                      'id': userid,
                      'u_login': bool(True),
                        'u_name': user.display_name,
                        'u_realname': user.real_name,
                        'u_email': user.email,
                        'g_hash': g_hash,
                        'u_created': user.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                        'u_lastlogin': "",
                        'u_logincount': user.logincount,
                        'u_version': user.assigned_version,
                        'u_isadmin': user.is_admin,
                        'u_isactive': user.is_active}
            if (user.lastlogin):
              result['u_lastlogin'] = user.lastlogin.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S")
        else:
          result['message'] = "Unable to retrieve selected user."
      else:
        result['message'] = "Not authenticated."     
      
      return self.respond(result) 

    def profile_user(self, id, **kwargs):
      utc = UTC()
      result = {'status':'error',
                'message':''}
      auser = self.auth.get_user_by_session()
      if auser:
        user = User.get_by_id(long(id))
        if user:
          email_hasher = hashlib.md5()
          email_hasher.update(user.email.lower())
          g_hash = email_hasher.hexdigest()
          if (not user.real_name):
            user.real_name = user.display_name #default to display name
            user.put()
          result = {'status':'success',
                    'id': id,
                      'u_name': user.display_name,
                      'u_realname': user.real_name,
                      'g_hash': g_hash,
                      'u_isadmin': user.is_admin}
        else:
          result['message'] = "Unable to retrieve selected user."
      else:
        result['message'] = "Not authenticated."
      
      return self.respond(result) 
      
    def get_user_by_id(self, id, **kwargs):
      utc = UTC()
      result = {'status':'error',
                'message':''}
      auser = self.auth.get_user_by_session()
      if auser:
        user = User.get_by_id(long(id))
        if user:
          email_hasher = hashlib.md5()
          email_hasher.update(user.email.lower())
          g_hash = email_hasher.hexdigest()
          if (not user.real_name):
            user.real_name = user.display_name #default to display name
            user.put()
          result = {'status':'success',
                    'id': id,
                      'u_name': user.display_name,
                      'u_realname': user.real_name,
                      'u_email': user.email,
                      'g_hash': g_hash,
                      'u_created': user.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                      'u_lastlogin': "",
                      'u_logincount': user.logincount,
                      'u_version': user.assigned_version,
                      'u_isadmin': user.is_admin,
                      'u_isactive': user.is_active}
          if (user.lastlogin):
            result['u_lastlogin'] = user.lastlogin.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S")
        else:
          result['message'] = "Unable to retrieve selected user."
      else:
        result['message'] = "Not authenticated."
      
      return self.respond(result) 
    
    def list_user(self, **kwargs):
      result = {'status':'error',
                'message':''}
      auser = self.auth.get_user_by_session()
      if auser:
        entities = User.search_users_by_name()
        result = {'status':'success',
                  'method':'list_user',
                  'en_type': 'User',
                  'entities': entities}
      else:
        result['message'] = "Not authenticated."
      return self.respond(result)

    def search_user(self, criteria, **kwargs):
      result = {'status':'error',
                'message':''}
      auser = self.auth.get_user_by_session()
      if auser:
        entities = User.search_users_by_name(criteria=criteria)
        result = {'status':'success',
                  'method':'search_user',
                  'en_type': 'User',
                  'entities': entities}
      else:
        result['message'] = "Not authenticated."
      return self.respond(result)
            
class LogoutPage(BaseHandler):
    def get(self):
      self.auth.unset_session()
      # User is logged out, let's try redirecting to login page
      try:
          self.redirect(self.auth_config['login_url'])
      except (AttributeError, KeyError), e:
          return "User is logged out"

webapp2_config = {}
webapp2_config['webapp2_extras.sessions'] = {
		'secret_key': 'n\xd99\xd4\x01Y\xea5/\xd0\x8e\x1ba\\:\x91\x10\x16\xbcTA\xe0\x87lf\xfb\x0e\xd2\xc4\x15\\\xaf\xb0\x91S\x12_\x86\t\xadZ\xae]\x96\xd0\x11\x80Ds\xd5\x86.\xbb\xd5\xcbb\xac\xc3T\xaf\x9a+\xc5',
	}

application = webapp2.WSGIApplication([
    webapp2.Route('/user/getuser', handler=GetUser, handler_method='get_user'),
    webapp2.Route('/user/getuser/<id>', handler=GetUser, handler_method='get_user_by_id'),
    webapp2.Route('/user/listuser', handler=GetUser, handler_method='list_user'),
    webapp2.Route('/user/listuser/<criteria>', handler=GetUser, handler_method='search_user'),
    webapp2.Route('/user/profileuser/<id>', handler=GetUser, handler_method='profile_user'),
    webapp2.Route('/user/edituser', handler=GetUser, handler_method='edit_user'),
    webapp2.Route('/user/logout', handler=LogoutPage),
    webapp2.Route('/user/janrain', handler=RPXTokenHandler)],
    config=webapp2_config,
    debug=True)