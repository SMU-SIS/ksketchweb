'''
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
'''

"""Users and OAuth2 Login Handler.

@created: Goh Kian Wei (Brandon), Kevin Koh, Shannon Lim, Tony Tran, Samantha Wee, Wong Si Hui
@code_adapted_from: Chris Boesch, Daniel Tsou
"""
"""
Note to self: json.loads = json string to objects. json.dumps is object to json string.
"""    

import datetime
import hashlib
import webapp2
import random
import httplib2
import logging
from apiclient import errors
from webapp2_extras import auth
from webapp2_extras import sessions
from apiclient.discovery import build
from webapp2_extras.appengine.auth.models import Unique
from oauth2client.client import flow_from_clientsecrets
from sendgrid import Sendgrid
from sendgrid import Message
from appengine_config import _ConfigDefaults
import json
from google.appengine.api import mail
from google.appengine.ext import db

class UTC(datetime.tzinfo):
  def utcoffset(self, dt):
    return datetime.timedelta(hours=0)
    
  def dst(self, dt):
    return datetime.timedelta(0)
    
  def tzname(self, dt):
    return "UTC"
    

class Unique(db.Model):
  @classmethod
  def check(cls, scope, value):
    def tx(scope, value):
      key_name = "U%s:%s" % (scope, value,)
      ue = Unique.get_by_key_name(key_name)
      if ue:
        raise UniqueConstraintViolation(scope, value)
      ue = Unique(key_name=key_name)
      ue.put()
    db.run_in_transaction(tx, scope, value)

class UniqueConstraintViolation(Exception):
  def __init__(self, scope, value):
    super(UniqueConstraintViolation, self).__init__("Value '%s' is not unique within scope '%s'." % (value, scope, ))

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
  is_approved        = db.BooleanProperty() #User parental consent status
  birth_month        = db.IntegerProperty() #User birth month
  birth_year         = db.IntegerProperty() #User birth year
  parent_email       = db.StringProperty()  #email add of User's parent
  contact_studies    = db.BooleanProperty() #User option for participation in studies
  contact_updates    = db.BooleanProperty() #User option for participation in updates
  encrypted          = db.BooleanProperty(default=True) #Encryption status

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
      if (user.parent_email != 'not required') == True:
        user.parent_email = Crypto.decrypt(user.parent_email)
      result = {'status':'success',
                'id': userid,
                'u_login': bool(True),
                'u_name': Crypto.decrypt(user.display_name),
                'u_realname': Crypto.decrypt(user.real_name),
                'u_email': Crypto.decrypt(user.email),
                'g_hash': g_hash,
                'u_created': user.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'u_lastlogin': "",
                'u_logincount': user.logincount,
                'u_version': user.assigned_version,
                'u_isadmin': user.is_admin,
                'u_isactive': user.is_active,
                'is_approved': user.is_approved,
                'birth_month': user.birth_month,
                'birth_year': user.birth_year,
                'parent_email': user.parent_email,
                'contact_studies': user.contact_studies,
                'contact_updates': user.contact_updates
              }
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
          return Crypto.decrypt(entity.display_name)
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
      if (user.parent_email != 'not required') == True:
        user.parent_email = Crypto.decrypt(user.parent_email)
      result = {'status':'success',
                'id': id,
                'u_login': bool(True),
                'u_name': Crypto.decrypt(user.display_name),
                'u_realname': Crypto.decrypt(user.real_name),
                'u_email': Crypto.decrypt(user.email),
                'g_hash': g_hash,
                'u_created': user.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                'u_lastlogin': "",
                'u_logincount': user.logincount,
                'u_version': user.assigned_version,
                'u_isadmin': user.is_admin,
                'u_isactive': user.is_active,
                'is_approved': user.is_approved,
                'birth_month': user.birth_month,
                'birth_year': user.birth_year,
                'parent_email': user.parent_email,
                'contact_studies': user.contact_studies,
                'contact_updates': user.contact_updates
                }
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
        if criteria.lower() in Crypto.decrypt(object.display_name).lower():
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
        if criteria.lower() in Crypto.decrypt(object.display_name).lower():
          include = True
        else:
          include = False

        if include:
          data = {'id': object.key().id(),
                  'u_name': Crypto.decrypt(object.display_name),
                  'u_realname': Crypto.decrypt(object.real_name)}
          entities.append(data)
    else:
      for object in objects:
        data = {'id': object.key().id(),
                'u_name': Crypto.decrypt(object.display_name),
                'u_realname': Crypto.decrypt(object.real_name)}
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
        decoded_display_name = Crypto.decrypt(object.display_name);
        if criteria != "":
          if criteria.lower() in decoded_display_name.lower():
            include = True
            
        if include:
          email_hasher = hashlib.md5()
          email_hasher.update(object.email.lower())
          g_hash = email_hasher.hexdigest()
          if (not object.real_name):
            object.real_name = decoded_display_name #default to display name
            object.put()
          if (object.parent_email != 'not required') == True:
            object.parent_email = Crypto.decrypt(object.parent_email)
          data = {'id': object.key().id(),
                  'u_name': decoded_display_name,
                  'u_realname': Crypto.decrypt(object.real_name),
                  'u_email': Crypto.decrypt(object.email),
                  'g_hash': g_hash,
                  'u_created': object.created.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S"),
                  'u_lastlogin': "",
                  'u_logincount': object.logincount,
                  'u_version': object.assigned_version,
                  'u_isadmin': object.is_admin,
                  'u_isactive': object.is_active,
                  'is_approved': object.is_approved,
                  'birth_month': object.birth_month,
                  'birth_year': object.birth_year,
                  'parent_email': object.parent_email,
                  'contact_studies': object.contact_studies,
                  'contact_updates': object.contact_updates
                }
          if (object.lastlogin):
            data['u_lastlogin'] = object.lastlogin.replace(tzinfo=utc).strftime("%d %b %Y %H:%M:%S")
          entities.append(data)
      result = {'method':'get_entities_by_id',
                'en_type':'User',
                'entities':entities}
      return result
  
  #Deletes a User's data
  @staticmethod
  def delete_entity(data):
    jsonData = json.loads(data)
    userid = long(jsonData['id'])

    user_entity = User.get_by_id(long(userid))
    user_entity.delete()

    result = {'status':'success',
              'message': 'You have successfully deleted this profile!'}

    logging.info("Delete: User data succesfully deleted")
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
          if (Crypto.decrypt(entity.display_name) != (jsonData['u_displayname'])) == False:
              entity.display_name = Crypto.encrypt(jsonData['u_displayname'])
          else:
            entity.display_name = jsonData['u_displayname']
        except (KeyError, ValueError):
          entity.display_name = entity.display_name
          
        try:
          if (Crypto.decrypt(entity.real_name) != (jsonData['u_realname'])) == False:
              entity.real_name = Crypto.encrypt(jsonData['u_realname'])
          else:
            entity.real_name = jsonData['u_realname']
        except (KeyError, ValueError):
          entity.real_name = entity.real_name
          
        try:
          entity.is_active = bool(jsonData['u_isactive'])
        except (KeyError, ValueError):
          entity.is_active = entity.is_active

        try:
          entity.birth_month = jsonData['birth_month']
        except (KeyError, ValueError):
          entity.birth_month = entity.birth_month

        try:
          entity.birth_year = jsonData['birth_year']
        except (KeyError, ValueError):
          entity.birth_year = entity.birth_year

        try:
          if jsonData['parent_email'] == 'not required':
            entity.parent_email = jsonData['parent_email']
          else:
            entity.parent_email = Crypto.encrypt(jsonData['parent_email'])
        except (KeyError, ValueError):
          entity.parent_email = entity.parent_email

        try:
          entity.is_approved = bool(jsonData['is_approved'])
        except (KeyError, ValueError):
          entity.is_approved = entity.is_approved

        try:
          entity.contact_updates = bool(jsonData['contact_updates'])
        except (KeyError, ValueError):
          entity.contact_updates = entity.contact_updates

        try:
          entity.contact_studies = bool(jsonData['contact_studies'])
        except (KeyError, ValueError):
          entity.contact_studies = entity.contact_studies

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
      data = json.loads(self.request.body)
      edit_type = data['edit_type']

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
        if edit_type == "parentApproval":
          profile_user_id = data['id']
          result = User.edit_entity(self.request.body, profile_user_id)
        else:
          result['message'] = "Not authenticated."   
          
      return self.respond(result) 

    #Handler for deleteing User
    def delete_user(self, **kwargs): #/user/edituser
      result = User.delete_entity(self.request.body)
      result = Sketch.delete_sketch_by_user(self.request.body)
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
          result['u_login'] = bool(True)
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

    #new implementation
    def get_user_mobile(self):
      userid = self.request.get("id")

      result = {'status':'Error',
                'u_login': bool(False),
                'message':''}

      if userid:
        result = User.get_entity(long(userid), result)
        result['u_login'] = bool(True)
      else:
        result['message'] = "Unable to retrieve selected user."
      
      return self.respond(result)
    
    #Handler for redirecting page with a user's id for mobile implementation
    def url_user(self): #/user/urlUser
      auser = self.auth.get_user_by_session()
      if auser:
        userid = auser['user_id']
        strid = str(userid)
        self.redirect(('/app/login_successful.html?id=' + strid).encode('ascii'))
      else:
        self.redirect('/app/index.html')

    #Handler for redirecting page with a user's id for mobile implementation
    def url_user_v2(self): #/user/urlUser
      auser = self.auth.get_user_by_session()
      if auser:
        userid = auser['user_id']
        strid = str(userid)
        token = auser['token']
        self.redirect(('/app/login_successful.html?id=' + strid+'&token='+token).encode('ascii'))
      else:
        self.redirect('/app/index.html')

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
    
    #Handler for retrieving a particular User's profile (partial) data
    def profile_user_unauthenticated(self, **kwargs): #/user/profileuser
      utc = UTC()
      result = {'status':'Error',
                'message':''}
      result = User.get_profile(self.request.body, result)
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

    #Handler for parent to approve a User
    def edit_approval(self): #/user/edituser
      userid = self.request.get("id")
      urltype = self.request.get("type")

      result = {'status':'Error',
                'u_login': bool(False),
                'message':''}

      if userid:
        result = User.get_entity(long(userid), result)
        status = result['status']

      if status == 'success':
        approve_state = result['is_approved']

        if approve_state:
          #implement backdoor for parent to view profile
          self.redirect('/app/index.html')
        else:
          if urltype == "approve":
            self.redirect(('/app/approval.html?id=' + userid).encode('ascii'))
          else:
            self.redirect(('/app/profile_delete.html?id=' + userid).encode('ascii'))
      else:
        self.redirect('/app/index.html')

    #Handler for parent to view user profile
    def parental_view(self): #/user/monitor
      userid = self.request.get("id")
      urltype = self.request.get("type")
      exist = True

      result = {'status':'Error',
                'u_login': bool(False),
                'message':''}

      if userid:
        result = User.get_entity(int(userid), result)
        
        if result['status'] == 'success':
          #check if user is under 18
          age = 0

          birth_month = result['birth_month']
          birth_year = result['birth_year']
          
          date = '30/' + str(birth_month) + '/' + str(birth_year)
          slist = date.split("/")
          d = datetime.date(int(slist[2]),int(slist[1]),int(slist[0]))
          born = datetime.datetime(d.year, d.month, d.day)
          today = datetime.datetime.now()

          try: 
              birthday = born.replace(year=today.year)
          except ValueError: # raised when birth date is February 29 and the current year is not a leap year
              birthday = born.replace(year=today.year, day=born.day-1)
          if birthday > today:
              age =  today.year - born.year - 1
          else:
              age = today.year - born.year
          
          if age < 18:
            self.redirect(('/app/profile.html?id=' + userid + "&type=" + urltype).encode('ascii'))
          else:
            self.redirect(('/app/index.html').encode('ascii'))
        else:
          self.redirect(('/app/index.html').encode('ascii'))
      else:
          self.redirect(('/app/index.html').encode('ascii'))

    #Handler to send approval email to parent of User
    def send_approval_email(self, **kwargs): #user/parentapproval
      utc = UTC()
      result = {'status':'Error',
                'u_login': bool(False),
                'message':''}
      auser = self.auth.get_user_by_session()
      if auser:
        userid = auser['user_id']
        if userid:
          result = User.get_entity(userid, result)
          result['u_login'] = bool(True)
       
        to_addr = result['parent_email']
      
      #generate random string
      alphabet = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
      pw_length = 50
      token_approve = ""
      token_disapprove = ""
      type_1 = "approve"
      type_2 = "disapprove"

      for i in range(pw_length):
          next_index1 = random.randrange(len(alphabet))
          next_index2 = random.randrange(len(alphabet))
          token_approve = token_approve + alphabet[next_index1]
          token_disapprove = token_disapprove + alphabet[next_index2]

      url_approve = self.uri_for('user_approval', type=type_1, token=token_approve, id=userid)
      url_disapprove = self.uri_for('user_approval', type=type_2, token=token_disapprove, id=userid)

      if not mail.is_email_valid(to_addr):
        # Return an error message...
        result['status'] = 'fail'
        pass

      strMessage = "Dear Parent, \n\
      \n\
K-Sketch would like to request permission for your child, "+ result['u_name'] + ", to participate in using our system. \n\
      \n\
Please click the following link to activate your child's account: " + "http://" +_ConfigDefaults.ksketch_HOSTNAME + url_approve + "\n\
      \n\
Please click the following link to cancel participation: " + "http://"+_ConfigDefaults.ksketch_HOSTNAME + url_disapprove + "\n\
\n\
\n\
K-Sketch Team"
      
      # make a secure connection to SendGrid
      s = Sendgrid(_ConfigDefaults.ksketch_SENDGRID_username, _ConfigDefaults.ksketch_SENDGRID_password, secure=True)

      # make a message object
      msg = Message(_ConfigDefaults.ksketch_EMAIL, "K-Sketch: Approval for Registration", strMessage, "")

      # add a recipient
      msg.add_to(to_addr)

      # use the Web API to send your message
      s.web.send(msg)

      #message.send()
      return self.respond(result)

    #Handler to send complete registration email to parent of User
    def send_complete_email(self, **kwargs): #/user/parentcomplete
      jsonData = json.loads(self.request.body)
      userid = long(jsonData['id'])

      result = {'status':'Error',
                'u_login': bool(False),
                'message':''}

      result = User.get_entity(userid, result)
      to_addr = result['parent_email']

      if not mail.is_email_valid(to_addr):
        # Return an error message...
        result['status'] = 'fail'
        pass

      type_1 = "parent"
      url_monitor = self.uri_for('user_monitor', type=type_1, id=userid)

      strMessage = "Dear Parent, \n\
      \n\
Thank you for allowing your child, "+ result['u_name'] + ", to participate in using K-Sketch. \n\
      \n\
To view your child's sketches, click on: " + "http://" + _ConfigDefaults.ksketch_HOSTNAME + url_monitor + "\n\
      \n\
Please bookmark this link to easily access your child's profile in the future.\n\
\n\
\n\
K-Sketch Team"
      
      # make a secure connection to SendGrid
      s = Sendgrid(_ConfigDefaults.ksketch_SENDGRID_username, _ConfigDefaults.ksketch_SENDGRID_password, secure=True)

      # make a message object
      msg = Message(_ConfigDefaults.ksketch_EMAIL, "K-Sketch: Registration Complete", strMessage, "")

      # add a recipient
      msg.add_to(to_addr)

      # use the Web API to send your message
      s.web.send(msg)

      #message.send()
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
#Class and handler for OAuth Authentication
class NoUserIdException(Exception):
  """Error raised when no user ID could be retrieved."""

def get_user_info(credentials):
      user_info_service = build(
          serviceName='oauth2', version='v2',
          http=credentials.authorize(httplib2.Http()))
      user_info = None
      try:
        user_info = user_info_service.userinfo().get().execute()
      except errors.HttpError, e:
        logging.error('An error occurred: %s', e)
      if user_info and user_info.get('id'):
        return user_info
      else:
        raise NoUserIdException()
class OAuthTokenHandler(BaseHandler):
    def login(self):
        flow = flow_from_clientsecrets('client_secrets.json',
                               scope=['https://www.googleapis.com/auth/userinfo.email','https://www.googleapis.com/auth/userinfo.profile'],
                               redirect_uri='http://'+_ConfigDefaults.ksketch_HOSTNAME +'/user/oauth2callback')
        auth_uri = flow.step1_get_authorize_url()
        #auth_uri ="https://accounts.google.com/o/oauth2/auth?client_id=" + flow.client_id + "&scope=https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email" + "&immediate=false&response_type=token&redirect_uri=http://localhost:8080/oauth2callback"
        self.redirect(str(auth_uri))
    """Receive the POST from RPX with our user's login information."""
    def oauth2callback(self):
        flow = flow_from_clientsecrets('client_secrets.json',
                               scope=['https://www.googleapis.com/auth/userinfo.email','https://www.googleapis.com/auth/userinfo.profile'],
                               redirect_uri='http://'+_ConfigDefaults.ksketch_HOSTNAME + '/user/oauth2callback')
        code = self.request.get('code')
        credentials = flow.step2_exchange(code)
        user_info = get_user_info(credentials)

        if user_info:
          # extract some useful fields
          oid = user_info['id']
          email = Crypto.encrypt(user_info['email'])
          try:
              display_name = Crypto.encrypt(user_info['name'])
          except KeyError:
              display_name = Crypto.encrypt(email.partition('@')[0])

            # check if there is a user present with that auth_id
          exist = True
          user = self.auth.store.user_model.get_by_auth_id(oid)
          if not user:
              user = self.auth.store.user_model.get_by_auth_id("https://www.google.com/profiles/"+oid)
          if not user:
              #Starting appver is always 1.0.
              appver = 1.0

              success, user = self.auth.store.user_model.create_user(oid, email=email, display_name=display_name, real_name=display_name, logincount=0,
                                                                          assigned_version=appver, is_admin=False, is_active=True, is_approved=False,
                                                                          birth_month=0, birth_year=0, parent_email="", contact_studies=True,
                                                                          contact_updates=True)
              logging.info('New user created in the DS')

              #update AppUserCount when adding
              AppUserCount.get_and_increment_counter(appver)
              exist = False

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
          db.delete(Unique.all())
          self.session.add_flash('You have successfully logged in', 'success')
          if exist:
              if user.is_approved:
                self.redirect('/app/profile.html')
              else:
                self.redirect('/app/register.html')
          else:
              self.redirect('/app/register.html')
        else:
            self.session.add_flash('There was an error while processing the login', 'error')
            self.redirect('/')

#Configuration and URI mapping
webapp2_config = {}

webapp2_config['webapp2_extras.sessions'] = {
    'secret_key': 'n\xd99\xd4\x01Y\xea5/\xd0\x8e\x1ba\\:\x91\x10\x16\xbcTA\xe0\x87lf\xfb\x0e\xd2\xc4\x15\\\xaf\xb0\x91S\x12_\x86\t\xadZ\xae]\x96\xd0\x11\x80Ds\xd5\x86.\xbb\xd5\xcbb\xac\xc3T\xaf\x9a+\xc5',
}

application = webapp2.WSGIApplication([
    webapp2.Route('/user/approval', handler=GetUser, name='user_approval', handler_method='edit_approval'),
    webapp2.Route('/user/monitor', handler=GetUser, name='user_monitor', handler_method='parental_view'),
    webapp2.Route('/user/getusermobile', handler=GetUser, name='user_mobile_login', handler_method='get_user_mobile'),
    webapp2.Route('/user/getuser', handler=GetUser, handler_method='get_user'),
    webapp2.Route('/user/getuserid', handler=GetUser, handler_method='get_user_by_id'),
    webapp2.Route('/user/urlUser', handler=GetUser, handler_method='url_user'),
    webapp2.Route('/user/urlUserV2', handler=GetUser, handler_method='url_user_v2'),
    webapp2.Route('/user/listuser', handler=GetUser, handler_method='list_user'),
    webapp2.Route('/user/profileuser', handler=GetUser, handler_method='profile_user'),
    webapp2.Route('/user/profileuser2', handler=GetUser, handler_method='profile_user_unauthenticated'),
    webapp2.Route('/user/edituser', handler=GetUser, handler_method='edit_user'),
    webapp2.Route('/user/deleteuser', handler=GetUser, handler_method='delete_user'),
    webapp2.Route('/user/parentapproval', handler=GetUser, handler_method='send_approval_email'),
    webapp2.Route('/user/parentcomplete', handler=GetUser, handler_method='send_complete_email'),
    webapp2.Route('/user/logout', handler=LogoutPage),
    webapp2.Route('/user/login', handler=OAuthTokenHandler,handler_method='login'),
     webapp2.Route('/user/oauth2callback', handler=OAuthTokenHandler,handler_method='oauth2callback')],
    config=webapp2_config,
    debug=True)
    
#Imports placed below to avoid circular imports
from counters import AppUserCount
from sketches import Sketch
from crypto import Crypto