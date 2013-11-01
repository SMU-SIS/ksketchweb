"""Users and Janrain Login Handler (RPX) Module

@created: Goh Kian Wei (Brandon), Kevin Koh, Shannon Lim, Tony Tran, Samantha Wee, Wong Si Hui
@code_adapted_from: Chris Boesch, Daniel Tsou
"""
"""
Note to self: json.loads = json string to objects. json.dumps is object to json string.
"""    

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
    
# Handles Users and its methods
class User(db.Model):
  email              = db.EmailProperty() #email address of User
  display_name       = db.StringProperty() #Display name of User. Used in Groups and as search criteria.
  real_name          = db.StringProperty() #Real name of user
  created            = db.DateTimeProperty(auto_now_add=True) #Date User joined the portal.
  modified           = db.DateTimeProperty(auto_now=True) #Date that User entity was modified.
  lastlogin          = db.DateTimeProperty() #Last login date of User
  logincount         = db.IntegerProperty() #No. of times User has logged in.
  assigned_version   = db.FloatProperty() #Application version assigned to user
  is_admin           = db.BooleanProperty() #User administrator status
  is_active          = db.BooleanProperty() #User active status

  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
  
  #Handler wrapper method to call get_entity via JSON POST
  @staticmethod
  def get_entity_wrapper(data, userid=0):
    result = {}
    jsonData = json.loads(data)
    otherid = 0
    try:
      otherid = long(jsonData['id'])
    except (KeyError, ValueError):
      otherid = 0
      
    
    if otherid != 0:
      result = {'status':'Error',
                'message':''}
      result = User.get_entity(otherid, result)
    else:
      result = {'status':'Error',
                'u_login': bool(False),
                'message':''}
      result = User.get_entity(userid, result)
    return result

  #Retrieves a particular User
  @staticmethod
  def get_entity(userid, default):
    utc = UTC()
    result = default
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
    return result

  #Retrieves a User's display name
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
        
  #Retrieves a User's email hash for profile image purposes (Gravatar)
  @staticmethod
  def get_image(model_id):
    #Retrieves display name
    if int(model_id) == 0:
      return ""
    else:
      try:
        entity = User.get_by_id(int(model_id))
        
        if entity:
          email_hasher = hashlib.md5()
          email_hasher.update(entity.email.lower())
          g_hash = email_hasher.hexdigest()            
          return g_hash
        else:
          return ""
      except ValueError:
        return ""      
      
  #Retrieves a User's profile.
  #This is a condensed version of the User data, shown when viewing another User's profile page.
  @staticmethod
  def get_profile(data, default):
    utc = UTC()
    result = default
    jsonData = json.loads(data)
    id = long(jsonData['id'])
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
                  'u_isadmin': user.is_admin,
                  'u_isactive': user.is_active}
    else:
      result['message'] = "Unable to retrieve selected user."
    return result

  #Checks if a User is an administrator
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

  #Gets possible IDs of Users that have similar display names to the criteria
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
        
  #Gets basic data of Users that have similar display names to the criteria
  @staticmethod
  def search_users_by_name(data):
    jsonData = json.loads(data)
    criteria = jsonData['criteria'].strip()
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
    
    #Gets Users by criteria
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
            
  #Edits a User's data
  @staticmethod
  def edit_entity(data, userid):
    jsonData = json.loads(data)
    model_id = long(jsonData['id'])
    result = {}
    
    edit_check = False
    if userid == model_id:
      edit_check = True
    elif User.check_if_admin(userid):
      edit_check = True
      
    if edit_check:    
      entity = User.get_by_id(long(model_id))
      if entity:
        try:
          entity.display_name = jsonData['u_displayname']
        except (KeyError, ValueError):
          entity.display_name = entity.display_name
          
        try:
          entity.real_name = jsonData['u_realname']
        except (KeyError, ValueError):
          entity.real_name = entity.real_name
          
        try:
          entity.is_active = bool(jsonData['u_isactive'])
        except (KeyError, ValueError):
          entity.is_active = entity.is_active
          #Other fields to be added as necessary.
        entity.put()
      
        result = {'status': 'success',
                'method':'edit_entity',
                'en_type':'User'}
      else:
        result = {'status': 'Error',
                'message': 'Unable to retrieve selected user.'}
    else:
      result = {'status': 'Error',
              'message': 'You are not allowed to edit this profile.',
              'submessage': 'Only the original user or an administrator may do so.'}
              
    return result

#Basic URI Handler for auth
class BaseHandler(webapp2.RequestHandler):
    """
      BaseHandler for all requests
       Holds the auth and session properties so they are reachable for all requests
    """
    
    #Methods for retrieving authentication
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
    
#Class and handler for Janrain Authentication    
class RPXTokenHandler(BaseHandler):
    """Receive the POST from RPX with our user's login information."""
    def post(self): #/user/janrain
        token = self.request.get('token')
        url = 'https://rpxnow.com/api/v2/auth_info'
        args = {
            'format': 'json',
            'apiKey': '6c8271a5a23692efa86799f3438e3ac7b0525ac0',   #Change to api key provided in Janrain
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
            # check provider "Google"
          if info['providerName'] == "Google":
            oid = info['identifier']
            email = info.get('email', '')
            try:
              display_name = info['displayName']
            except KeyError:
              display_name = email.partition('@')[0]

            # check if there is a user present with that auth_id
            user = self.auth.store.user_model.get_by_auth_id(oid)
            if not user:
              #Starting appver is always 1.0.
              appver = 1.0
              
              success, user = self.auth.store.user_model.create_user(oid, email=email, display_name=display_name, real_name=display_name, logincount=0, assigned_version=appver, is_admin=False, is_active=True)
              logging.info('New user created in the DS')
              
              #update AppUserCount when adding
              AppUserCount.get_and_increment_counter(appver)
            
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
            self.redirect('/app/profile.html')
          else:
            self.session.add_flash('There was an error while processing the login', 'error')
            self.redirect('/')
        else:
          self.session.add_flash('There was an error while processing the login', 'error')
          self.redirect('/')

#Class for all User URI handlers
class GetUser(webapp2.RequestHandler):
        
    #Methods for retrieving authentication
    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    """Class which handles bootstrap procedure and seeds the necessary
    entities in the datastore.
    """

    #Response wrapper for handler    
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
        
    #Handler for editing of User
    def edit_user(self, **kwargs): #/user/edituser
      utc = UTC()
      auser = self.auth.get_user_by_session()
      result = {'method':'edit_entity',
              'en_type':'User',
              'status':'Error',
              'message': ''}
      if auser:
        userid = auser['user_id']
        if userid:
          result = User.edit_entity(self.request.body, userid)
        else:
          result['message'] = "Unable to retrieve selected user."
      else:
        result['message'] = "Not authenticated."   
          
      return self.respond(result) 

    #Handler for a User to retrieve their own data after logging in
    def get_user(self, **kwargs): #/user/getuser
      utc = UTC()
      result = {'status':'Error',
                'u_login': bool(False),
                'message':''}
      auser = self.auth.get_user_by_session()
      if auser:
        userid = auser['user_id']
        if userid:
          result = User.get_entity(userid, result)
        else:
          result['message'] = "Unable to retrieve selected user."
      else:
        result['message'] = "Not authenticated."     
      
      return self.respond(result)
    
    #Handler for retrieving a particular User's full data
    def get_user_by_id(self, **kwargs): #/user/getuserid
      utc = UTC()
      result = {'status':'Error',
                'u_login': bool(False),
                'message':''}
      auser = self.auth.get_user_by_session()
      if auser:
        userid = auser['user_id']
        if userid:
          result = User.get_entity_wrapper(self.request.body, userid)
        else:
          result['message'] = "Unable to retrieve selected user."
      else:
        result['message'] = "Not authenticated."     
      
      return self.respond(result) 
      
    #Handler for retrieving a particular User's profile (partial) data
    def profile_user(self, **kwargs): #/user/profileuser
      utc = UTC()
      result = {'status':'Error',
                'message':''}
      auser = self.auth.get_user_by_session()
      if auser:
        result = User.get_profile(self.request.body, result)
        
      else:
        result['message'] = "Not authenticated."
      
      return self.respond(result) 
      
    #Handler for searching for Users by criteria
    def list_user(self, **kwargs): #/user/listuser
      result = {'status':'Error',
                'message':''}
      auser = self.auth.get_user_by_session()
      if auser:
        entities = User.search_users_by_name(self.request.body)
        result = {'status':'success',
                  'method':'list_user',
                  'en_type': 'User',
                  'entities': entities}
      else:
        result['message'] = "Not authenticated."
      return self.respond(result)
      
 #Handler for logging out and cancelling of session
class LogoutPage(BaseHandler):
    def get(self): #/user/logout
      self.auth.unset_session()
      # User is logged out, let's try redirecting to login page
      try:
          self.redirect(self.auth_config['login_url'])
      except (AttributeError, KeyError), e:
          return "User is logged out"

#Configuration and URI mapping
webapp2_config = {}
webapp2_config['webapp2_extras.sessions'] = {
		'secret_key': 'n\xd99\xd4\x01Y\xea5/\xd0\x8e\x1ba\\:\x91\x10\x16\xbcTA\xe0\x87lf\xfb\x0e\xd2\xc4\x15\\\xaf\xb0\x91S\x12_\x86\t\xadZ\xae]\x96\xd0\x11\x80Ds\xd5\x86.\xbb\xd5\xcbb\xac\xc3T\xaf\x9a+\xc5',
	}

application = webapp2.WSGIApplication([
    webapp2.Route('/user/getuser', handler=GetUser, handler_method='get_user'),
    webapp2.Route('/user/getuserid', handler=GetUser, handler_method='get_user_by_id'),
    webapp2.Route('/user/listuser', handler=GetUser, handler_method='list_user'),
    webapp2.Route('/user/profileuser', handler=GetUser, handler_method='profile_user'),
    webapp2.Route('/user/edituser', handler=GetUser, handler_method='edit_user'),
    webapp2.Route('/user/logout', handler=LogoutPage),
    webapp2.Route('/user/janrain', handler=RPXTokenHandler)],
    config=webapp2_config,
    debug=True)
    
#Imports placed below to avoid circular imports
from counters import AppUserCount
