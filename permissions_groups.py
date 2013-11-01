"""Permissions & Groups Module

@created: Goh Kian Wei (Brandon), Kevin Koh, Shannon Lim, Tony Tran, Samantha Wee, Wong Si Hui
@code_adapted_from: Chris Boesch, Daniel Tsou
"""
"""
Note to self: json.loads = json string to objects. json.dumps is object to json string.
"""      
import datetime
import os
import urllib
import urllib2

import webapp2
from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import json


#Handles public Permissions for a Sketch
class Permissions(db.Model):
  sketch_id = db.IntegerProperty() #SketchID of the Sketch Permissions is linked to
  view = db.BooleanProperty(required=True) #Public permissions for viewing
  edit = db.BooleanProperty(required=True) #Public permissions for editing
  comment = db.BooleanProperty(required=True) #Public permissions for commenting
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d

  #Adds Permissions for a Sketch. Called whenever a Sketch is created.
  @staticmethod
  def add(s_id, p_view, p_edit, p_comment):
    p_key = -1
    try:
      entity = Permissions.all().filter('sketch_id',long(s_id)).get()
      #Update existing permissions
      if entity:
        entity.view = bool(p_view)
        entity.edit = bool(p_edit)
        entity.comment = bool(p_comment)
        entity.put()
        
      #No existing permissions - create new permissions
      else:
        entity = Permissions(sketch_id = long(s_id),
                            view = bool(p_view),
                            edit = bool(p_edit),
                            comment = bool(p_comment))
        entity.put()
      p_key = entity.key().id()
    except:
      p_key = -1
    return p_key
    
  
  #Checks public Permissions for a Sketch  
  @staticmethod
  def check_permissions(sketch_id = 0):
    result = {'p_view':False,
              'p_edit':False,
              'p_comment':False}
              
    permissions = Permissions.all().filter('sketch_id', sketch_id).get()
    if permissions:
      result = {'p_view':permissions.view,
                'p_edit':permissions.edit,
                'p_comment':permissions.comment}
    return result

  #Method for retrieving overall access to a Sketch for a User.
  #Factors in Group membership (Sketch_Groups), Sketch ownership, and administrator status.
  #Administrators have automatic full access to all Sketches.
  #The owner of a Sketch has full access to all of their Sketches.
  @staticmethod
  def user_access_control(sketch_id = 0, user_id = 0):
    permissions = {'p_view':False,
                    'p_edit':False,
                    'p_comment':False}
    #Check if Admin - if true, grant FULL access
    if User.check_if_admin(user_id):
      permissions = {'p_view':True,
                    'p_edit':True,
                    'p_comment':True}
    #Check if Owner - if true, grant FULL access
    elif Sketch.check_if_owner(long(sketch_id), user_id):
      permissions = {'p_view':True,
                    'p_edit':True,
                    'p_comment':True}
    else:
      #Retrieve public permissions
      permissions = Permissions.check_permissions(long(sketch_id))
      
      #Retrieve group permissions
      group_permissions = Sketch_Groups.get_groups_for_sketch(long(sketch_id))
      user_groups = UserGroupMgmt.get_memberships(user_id)
      user_group_permissions = []
      for u_g in user_groups:
        group_id = u_g['group_id']
        for g_p in group_permissions:
          if long(group_id) == long(g_p['id']):
            user_group_permissions.append(g_p)
      #Apply group permissions
      for u_g_p in user_group_permissions:
        permissions['p_view'] = True
        if not permissions['p_edit']:
          permissions['p_edit'] = u_g_p['edit']
        if not permissions['p_comment']:
          permissions['p_comment'] = u_g_p['comment']
        if permissions['p_edit'] and permissions['p_comment']:
          break
    return permissions
    
  #Deletes permissions for a Sketch. Called when a Sketch is deleted.
  @staticmethod  
  def delete_by_sketch(sketch_id):
    theQuery = Permissions.all()
    theQuery = theQuery.filter('sketch_id =', long(sketch_id))
    theobject = theQuery.get()
    if theobject:
      theobject.delete()
    result = {'method':'delete_by_sketch',
              'en_type': 'Permissions',
              'sketchId': sketch_id}
    return result 
    
#Handles assignment of Sketches to Groups, and permissions access for said Groups to the Sketch. This supersedes the public access in Permissions.
#Groups that are assigned to a Sketch can automatically view said sketch.
class Sketch_Groups(db.Model):
  sketch_id = db.IntegerProperty() #SketchID of the Sketch
  group_id = db.IntegerProperty(required=True) #Id of the Group
  edit = db.BooleanProperty(required=True) #Group permissions for editing
  comment = db.BooleanProperty(required=True) #Group permissions for commenting
  #It is assumed that a sketch that belongs to a group
  #can be viewed by said group - thus, a "view" variable is
  #unnecessary.
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d
  
  #Adds Sketch_Groups for a Sketch. Called when a Sketch is created.
  @staticmethod
  def add(s_id, group_permissions):
    count = 0
    current_perm = Sketch_Groups.all().filter('sketch_id', long(s_id)).fetch(limit=None)
    for c_p in current_perm:
      c_p.delete()
    try:
      for g_p in group_permissions:
        edit = False
        comment = False
        try:
          edit = bool(g_p['edit'])
        except (KeyError, ValueError):
          edit = False
        try:
          comment = bool(g_p['comment'])
        except (KeyError, ValueError):
          edit = False
          
        new_perm = Sketch_Groups(sketch_id = long(s_id),
                            group_id = long(g_p['id']),
                            edit = edit,
                            comment = comment)
        new_perm.put()
        count += 1
    except:
      count = 0
    return count
  
  #Gets Groups that are linked to a Sketch
  @staticmethod
  def get_groups_for_sketch(sketch_id=0):
    theQuery = Sketch_Groups.all().filter('sketch_id', sketch_id)
    objects = theQuery.run()
    
    entities = []
    for object in objects:
      data = {'group_name': Group.get_name(object.group_id)}
      entity = {'object_id': object.key().id(),
                'sketch_id': object.sketch_id,
                'id': object.group_id,
                'data':data,
                'edit': object.edit,
                'comment':object.comment}
      entities.append(entity)
    return entities    
  
  #Gets Sketches for a particular Group
  @staticmethod
  def get_sketches_for_group(group_id=0):
    theQuery = Sketch_Groups.all().filter('group_id', group_id)
    objects = theQuery.run()
    
    entities = []
    for object in objects:
      data = {'id': object.key().id(),
              'sketch_id': object.sketch_id,
              'group_id': object.group_id,
              'group_name': Group.get_name(object.group_id),
              'edit': object.edit,
              'comment':object.comment}
      entities.append(data)
    return entities
  
  #Deletes Sketch_Groups by Sketch. Called when a Sketch is deleted.
  @staticmethod  
  def delete_by_sketch(sketch_id):
    theQuery = Sketch_Groups.all()
    theQuery = theQuery.filter('sketch_id', long(sketch_id))
    objects = theQuery.run()
    count = 0
    for object in objects:
      object.delete()
      count += 1
    result = {'method':'delete_by_sketch',
              'en_type': 'Sketch_Groups',
              'sketchId': sketch_id,
              'count': count}
    return result
  
  #Deletes Sketch_Groups by Group. Called when a Group is deleted.  
  @staticmethod  
  def delete_by_group(group_id):
    theQuery = Sketch_Groups.all()
    theQuery = theQuery.filter('group_id', long(group_id))
    objects = theQuery.run()
    count = 0
    for object in objects:
      object.delete()
      count += 1
    result = {'method':'delete_by_group',
              'en_type': 'Sketch_Groups',
              'groupId': group_id,
              'count': count}
    return result
    
#Handles Groups and its methods    
class Group(db.Model):
  group_name = db.StringProperty(required=True) #Name of the Group
  group_sketches = db.TextProperty()
  created = db.DateTimeProperty(auto_now_add=True) #The time that the model was created
  
  def to_dict(self):
       d = dict([(p, unicode(getattr(self, p))) for p in self.properties()])
       d["id"] = self.key().id()
       return d

  #Creates a Group
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
                    'method': 'add',
                    'en_type': 'Group',
                    'g_name': jsonData['group_name'],
                    'u_id': jsonData['user_id'],
                    'role': "Founder"}
        else:
          result = {'status': 'error',
                    'message': 'The name you chose is already in use!',
                    'submessage': 'Please choose a different group name!'}
              
    return result
    
  #Retrieves the name of a Group   
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

  #Retrieves a particular Group     
  @staticmethod
  def get_entity(data):
    jsonData = json.loads(data)
    model_id = long(jsonData['id'])
    utc = UTC()
    result = {}
    theobject = Group.get_by_id(long(model_id))
    if theobject:
      user_groups_query = UserGroupMgmt.all().filter('group_id', theobject.key().id()).run()
      u_groups = []
      
      if user_groups_query:
        for u_g in user_groups_query:
          user_name = User.get_name(u_g.user_id)
          u_entity = {'user': user_name,
                      'g_hash': User.get_image(u_g.user_id),
                      'user_id': u_g.user_id,
                      'group_id': model_id,#placeholder
                      'role': u_g.role}
          u_groups.append(u_entity)    
      
      result = {'status':'success',
                'method':'get_entity',
                'en_type': 'Group',
                'id': model_id,
                'group_name': theobject.group_name,
                'u_groups': u_groups
                }
    else:
      result = {'status':'Error',
                'message':'There was an error in loading the group you wanted.',
                'submessage':'Please check the URL and try again later.'}
    return result
    

  #Deletes a particular Group and related entities.
  #Only a Group Founder may delete a Group.
  @staticmethod
  def remove(data, userid):
    jsonData = json.loads(data)
    model_id = long(jsonData['id'])
    
    theobject = Group.get_by_id(long(model_id))
    
    check_founder = UserGroupMgmt.all().filter('group_id', model_id).filter('role', "Founder").get()
    result = {}
    if theobject and check_founder:
      can_delete = False
      if check_founder.user_id == userid:
        can_delete = True
        
      if can_delete:
        group_name = theobject.group_name
        theobject.delete()
        user_groups_query = UserGroupMgmt.all().filter('group_id', model_id).run()
        
        pending = Notification.all().filter('notification_type','GROUPINVITE').run()
        
        for p in pending:
          u_g = UserGroupMgmt.get_by_id(p.relevant_id)
          if u_g and u_g.group_id == model_id:
            p.notification_type = 'GROUPDELCANCEL'
            p.other_info = group_name
            p.n_date = datetime.datetime.now()
            p.put()
        
        Sketch_Groups.delete_by_group(model_id)
        
        for u_g in user_groups_query:
          
          if u_g.role == 'Member':
            Notification.add(u_g.user_id, "GROUPDELETE", userid, group_name, 0)
          u_g.delete()
        result = {'status': 'success',
                  'method': 'remove',
                  'en_type': 'Group',
                  'message': "The group '" + group_name + "' has been successfully deleted."}
      else:
        result = {'status': 'Error',
                  'message': "You have to be the Founder in order to delete the group." }
    else:
      result = {'status': 'Error',
                'message': "Unable to delete the group!"}
    return result
    
#Handles membership of Users in a particular Group, as well as Group invites/expulsion etc.    
class UserGroupMgmt(db.Model):
  user_id = db.IntegerProperty(required=True) #ID of the User in the Group
  group_id = db.IntegerProperty(required=True) #ID of the Group the User belongs to
  role = db.StringProperty(required=True) #User's role in the Group (Founder/Member/Pending)
  
  #Invites a User to a Group
  #User's status in Group is "Pending" unless they accept the invite
  #A "Pending" User is not considered a Group member for purposes of Permissions
  @staticmethod
  def add(data, other_user):
    #update ModelCount when adding
    jsonData = json.loads(data)
    result = {'status':'error',
              'message':'There was an error in sending the invite.',
              'submessage':'Please try again later.'}    
    if jsonData['group_id'] != 0:
      users = jsonData['users']
      invited = []
      theQuery = UserGroupMgmt.all().filter('group_id', long(jsonData['group_id']))
      objects = theQuery.fetch(limit=None)
      for user in users:
        user_group_exists = False
        for object in objects:
          if long(user['id']) == long(object.user_id):
            user_group_exists = True
            break
        if not user_group_exists:
          entity = UserGroupMgmt(user_id=long(user['id']),
                                group_id=long(jsonData['group_id']),
                                role="Pending")
        
          entity.put()
          
          Notification.add(long(user['id']), "GROUPINVITE", long(other_user), "",entity.key().id()) 
          invited.append(user['u_name'])
      
      if len(invited) > 0:
        result = {'status': 'success',
              'invited': invited,
              'group_id': jsonData['group_id']}  
      else:
        result = {'status':'error',
                'message':'Please select valid user(s) to invite.'}   
        
    else:
      result = {'status':'error',
              'message':'Please select valid user(s) to invite.'}   
    return result
    
  
  #Gets members of a particular Group
  @staticmethod
  def get_entities(data):
    jsonData = json.loads(data)
    criteria = long(jsonData['id'])
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
          
        if object.role == "Pending":
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
              'en_type': 'UserGroupMgmt',
              'entities': entities}
    return result
    
  #Checks if Users belong to a Group by criteria
  @staticmethod
  def check_users(data):
  
    jsonData = json.loads(data)
    model_id = long(jsonData['id'])
    criteria = jsonData['criteria'].strip()
    
    theQuery = User.all()
    objects = theQuery.run()
    
    groupQuery = UserGroupMgmt.all().filter('group_id', int(model_id))
    groupObjects = groupQuery.fetch(limit=None)
    
    entities = []
    for object in objects:
      test = ""
      include = True
      if criteria != "":      
        if criteria.lower() in object.display_name.lower():
          include = True
        else:
          include = False
      
      for groupObject in groupObjects:
        test += " " + str(groupObject.user_id)
        if object.key().id() == groupObject.user_id:
          include = False
            
      if include:
        data = {'id': object.key().id(),
                'u_name': object.display_name,
                'u_realname': object.real_name}
        entities.append(data)
    return entities
    
  #Handles removal of a User from a Group
  #This covers a User leaving a Group, as well as expulsion by the Group's owner (Founder).
  @staticmethod
  def remove_user(data, userid):
    jsonData = json.loads(data)
    remove_id = long(jsonData['user_id'])
    role = jsonData['role']
    group_id = long(jsonData['group_id'])
    
    result = {}
    
    user_groups_query = UserGroupMgmt.all().filter('group_id', group_id).filter('user_id', remove_id).get()
    check_founder = UserGroupMgmt.all().filter('group_id', group_id).filter('role', "Founder").get()
    
    if user_groups_query and check_founder:
      if check_founder.user_id == userid or User.check_if_admin(userid):
        if userid != remove_id:
          user_groups_query.delete()
          result = {'status': 'success',
                    'method': 'remove_user',
                    'en_type': 'UserGroupMgmt',
                    'type': 'kick',
                    'message': 'You have expelled ' + User.get_name(remove_id) + ' the group "' + Group.get_name(group_id) + '".'}
          Notification.add(remove_id, "GROUPEXPEL", userid, "", group_id)
        else:
          result = {'status': 'Error',
                    'message': 'You cannot expel yourself if you are the Founder!',
                    'submessage': 'Pass the Founder position to someone else before trying to leave.'}
      elif remove_id == userid:
        user_groups_query.delete()
        result = {'status': 'success',
                  'method': 'remove_user',
                  'en_type': 'UserGroupMgmt',
                  'type': 'quit',
                  'message': 'You have left the group "' + Group.get_name(group_id) + '".'}
        Notification.add(check_founder.user_id, "GROUPLEAVE", remove_id, "", group_id) 
        
      else:
        result = {'status': 'Error',
                  'message': 'You cannot expel a member unless you are the founder!'}
    else:
      result = {'status': 'Error',
                'message': 'Unable to find the user to be expelled!'}
    return result
  
  #Passes ownership over a Group to another User in that Group.
  #A Group Founder may not leave a Group (unless they pass on the position), but they may delete it.
  @staticmethod
  def pass_founder(data, userid):
    jsonData = json.loads(data)
    pass_id = long(jsonData['user_id'])
    role = jsonData['role']
    group_id = long(jsonData['group_id'])
    
    result = {}
    
    user_groups_query = UserGroupMgmt.all().filter('group_id', group_id).filter('user_id', pass_id).get()
    check_founder = UserGroupMgmt.all().filter('group_id', group_id).filter('role', "Founder").get()
  
    if user_groups_query and check_founder:
      if check_founder.user_id == userid:
        if userid != pass_id:
          user_groups_query.role = "Founder";
          check_founder.role = "Member";
          user_groups_query.put()
          check_founder.put()
          
          
          Notification.add(pass_id, "GROUPPASSFOUNDER", check_founder.user_id, "", group_id) 
          result = {'status': 'Success',
                    'method': 'pass_founder',
                    'en_type': 'UserGroupMgmt',
                    'message': 'You have made ' + User.get_name(pass_id) + ' the Founder of the group "' + Group.get_name(group_id) + '".'}
        else:
          result = {'status': 'Error',
                  'message': 'You are already the Founder!'}
      else:
        result = {'status': 'Error',
                  'message': 'You are not the Founder of this group!'}
    else:
      result = {'status': 'Error',
                  'message': 'Unable to find the user to be given the Founder position!'}
    return result
  
  #Gets the Groups of a particular User
  @staticmethod
  def get_memberships(userid):
    entities = []
    try:
      theQuery = UserGroupMgmt.all().filter('user_id', long(userid))
      objects = theQuery.run()
      for object in objects:
        if object.role != "Pending":
          data = {'user_id': object.user_id,
                  'group_id': object.group_id,
                  'role': object.role}
          entities.append(data)
    except ValueError:
      entities = []
    return entities
    
  #Handles acceptance/rejection of a Group invite.
  @staticmethod
  def accept_reject(data, userid):
    jsonData = json.loads(data)
    result = {'status':'error',
              'message':'There was an error in processing the invitation.',
              'submessage':'Please try again later.'}
    status = str(jsonData['status'])
    u_g = UserGroupMgmt.get_by_id(int(jsonData['u_g']))
    founder = UserGroupMgmt.all().filter('group_id', u_g.group_id).filter('role', 'Founder').get()
    if status == "accept":
      u_g.role = "Member"
      u_g.put()
      Notification.add(founder.user_id, "GROUPACCEPT", int(userid), "", u_g.group_id)
      Notification.add(int(userid), "GROUPJOINCFM", 0, "", u_g.group_id)  
    else:
      u_g.delete()
      Notification.add(founder.user_id, "GROUPREJECT", int(userid), "", u_g.group_id) 
    
    old_notify = Notification.get_by_id(int(jsonData['n_id']))
    old_notify.delete()
    
    result = {'status': 'success',
              'method': 'accept_reject',
              'en_type': 'UserGroupMgmt',
              'message': 'You have successfully ' + jsonData['status'] + 'ed the group invitation.'}
    return result
 
#Imports placed below to avoid circular imports
from rpx import User, UTC
from sketches import Sketch
from notifications import Notification