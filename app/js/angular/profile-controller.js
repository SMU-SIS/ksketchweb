'use strict';

/* Controller for profile.html */

//angular.module('app', ['ngResource']);
function ProfileController($scope,$resource,sharedProperties, sharedFunctions){
    
	$scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "", 'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false, 'u_changed': 0};
  
  $scope.profile_user = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "g_hash": "", 'u_isadmin': false, 'u_isactive': false, 'u_changed': 0};
    
  $scope.backend_locations = [
    {url : sharedProperties.getBackendUrl(), urlName : 'remote backend' },       
    {url : 'localhost:8080', urlName : 'localhost' } ];

  $scope.showdetails = false;
  
  //Date (Time Zone) Format
  $scope.tzformat = function(utc_date) {
  
    var d = moment(utc_date, "DD MMM YYYY HH:mm:ss");
    return d.format("dddd, Do MMM YYYY, hh:mm:ss");
  };
  
  $scope.search = "";
  $scope.selected_search = "Name";
  
  $scope.newgroup = {};
  $scope.newgroup.data = {"group_name":"", "user_id":""};
  
  $scope.test = "-";
  $scope.profilemeta = {};
  $scope.profilemeta.data = {'id':0};
  
  $scope.editprofilemeta = {};
  $scope.editprofilemeta.data = {'id': 0,
                                 'u_displayname': "",
                                 'u_realname': ""};
                                 
  
  $scope.reload = false;
  $scope.heading = "";
  $scope.message = "";
  $scope.submessage = "";
  $scope.notify = "You have no new notification(s).";
  $scope.notify_icon = "icon-list-alt";
  
  
  //Search Query Filter
  $scope.query = function(item) {
      return !!((item.data.fileName.indexOf($scope.search || '') !== -1 || item.data.owner.indexOf($scope.search || '') !== -1));
  };

  $scope.predicate_users = '-data.fileName';
  

  //Replace this url with your final URL from the SingPath API path. 
  //$scope.remote_url = "localhost:8080";
<<<<<<< HEAD
  $scope.remote_url = "ksketchweb.appspot.com";
=======
  $scope.remote_url = sharedProperties.getBackendUrl();
  $scope.janrain_ref = sharedProperties.getJanrainAccount();
>>>>>>> 57f7773d73da6e3f5bb6a146206c037708c7111c
  $scope.waiting = "Ready";
  
  //resource calls are defined here

  $scope.Model = $resource('http://:remote_url/:model_type/:id',
                          {},{'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                             }
                      );
  
  $scope.getuser = function(){
    $scope.UserResource = $resource('http://:remote_url/user/getuser',
                        {'remote_url':$scope.remote_url},
                        {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                           });  
    $scope.waiting = "Loading";       
    $scope.UserResource.get(function(response) {
          var result = response;
          if (result.u_login === "True" || result.u_login === true) {
            $scope.User = result;
            $scope.User.u_created = $scope.tzformat($scope.User.u_created);
            
            if ($scope.User.u_lastlogin !== "") {
              $scope.User.u_lastlogin = $scope.tzformat($scope.User.u_lastlogin);
            }
            $scope.get_notification();            
          } else {
            $scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "",  'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false, 'u_changed': 0};
            if (navigator.userAgent.match(/MSIE\s(?!9.0)/))
            {
              var referLink = document.createElement("a");
              referLink.href = "index.html";
              document.body.appendChild(referLink);
              referLink.click();
            }
            else { window.location.replace("index.html");}
          }
    });
  }  
  
  $scope.setTest = function(test) {
    $scope.test = test;
  }
  
  $scope.get_profile = function() {
    var same = (parseInt($scope.test) === parseInt($scope.User.id));
    if ($scope.test === "-") {
      $scope.profile_user = $scope.User;
      $scope.grouplist();
      $scope.list();
      $scope.profile_meta();
      $scope.belong = true;
    } else if (same === true) {
      $scope.profile_user = $scope.User;
      $scope.grouplist();
      $scope.list();
      $scope.profile_meta();
      $scope.belong = true;
    
    } else {
      $scope.belong = false;
      $scope.profilemeta.data.id = $scope.test;
      $scope.ProfileUserResource = $resource('http://:remote_url/user/profileuser',
                                 {"remote_url":$scope.remote_url}, 
                                 {'save': {method: 'POST', params:{} }});
      $scope.waiting = "Loading";       
      var profilemeta = new $scope.ProfileUserResource($scope.profilemeta.data);
      profilemeta.$save(function(response) {
            var result = response;
            if (result.status === "success") {
              $scope.profile_user = result;
              $scope.list();
              $scope.grouplist();
              $scope.profile_meta();
            } else {
              if (navigator.userAgent.match(/MSIE\s(?!9.0)/))
              {
                var referLink = document.createElement("a");
                referLink.href = "index.html";
                document.body.appendChild(referLink);
                referLink.click();
              }
              else { window.location.replace("index.html");}
            }            
      });
    }
  }
  
  $scope.profile_meta = function() {
  
    $scope.editprofilemeta.data = {'id': $scope.profile_user.id,
                                 'u_displayname': $scope.profile_user.u_name,
                                 'u_realname': $scope.profile_user.u_realname};
  }
  
  $scope.change_profile = function() {
    if ($scope.belong === true) {
      if ($scope.editprofilemeta.data.u_displayname != $scope.profile_user.u_name
        || $scope.editprofilemeta.data.u_realname != $scope.profile_user.u_realname) {
        bootbox.confirm("Do you really wish to change your profile data?", function(changeAlert) {
          if (changeAlert === true) {
            $scope.edit_profile($scope.editprofilemeta.data);
          } else {
            $scope.editprofilemeta.data = {'id': $scope.profile_user.id,
                                           'u_displayname': $scope.profile_user.u_name,
                                           'u_realname': $scope.profile_user.u_realname};
          }
        });
      }
    } else {
      $scope.waiting = "Error";
      $scope.heading = "Oops...!";
      $scope.message = "You are not allowed to edit this profile.";
    }
  }
  
  $scope.edit_profile = function(meta) {
    if ($scope.belong === true) {
      $scope.EditUserResource = $resource('http://:remote_url/user/edituser',
                                {'remote_url':$scope.remote_url}, 
                                {'update': { method: 'PUT', params: {} }});
      var edit_user = new $scope.EditUserResource(meta);
      $scope.waiting = "Loading";
      edit_user.$update(function(response) {
            var result = response;
            if (result.status === 'success') {
              $scope.waiting = "Error";
              $scope.heading = "Success!";
              $scope.message = "You have successfully changed your profile!";
              $scope.reload = true;
            } else {
              $scope.waiting = "Error";
              $scope.heading = "Oops...!";
              $scope.message = result.message;
              $scope.submessage = result.submessage;
            }
      });
    }
  };
  
  $scope.addgroup = function(){
    $scope.newgroup.data.user_id = $scope.User.id;
    $scope.GroupResource = $resource('http://:remote_url/add/group', 
                  {"remote_url":$scope.remote_url}, 
                  {'save': { method: 'POST',    params: {} }});
 
    $scope.waiting = "Saving";
    var newgroup = new $scope.GroupResource($scope.newgroup.data);
    newgroup.$save(function(response) { 
            var result = response;
            $scope.newgroup.data = {"group_name":"", "user_id":""};
            $scope.grouplist();
            if (result.status === 'success') {
              $scope.waiting = "Error";
              $scope.heading = "Success!";
              $scope.message = "You have successfully founded the group '" + result.g_name + "'!";
            } else {
              $scope.waiting = "Error";
              $scope.heading = "Oops...!"
              $scope.message = result.message;
              $scope.submessage = result.submessage;
            }
          }); 
  };
  
  //To add key/value pairs when creating new objects
  $scope.add_key_to_item = function(){
    $scope.item.data[$scope.newItemKey] = $scope.newItemValue;
    $scope.newItemKey = "";
    $scope.newItemValue = "";
  };    
  
  $scope.grouplist = function() {
    $scope.groupmeta = {};
    $scope.groupmeta.data = {'id':$scope.profile_user.id};
    $scope.GroupListResource = $resource('http://:remote_url/list/group',
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Loading";  
    var groupmeta = new $scope.GroupListResource($scope.groupmeta.data);
    groupmeta.$save(function(response) {
        $scope.groups = response;
     });  
  }

  $scope.acknowledge = function() {
    if ($scope.reload === true) {
      if (navigator.userAgent.match(/MSIE\s(?!9.0)/))
      {
        var referLink = document.createElement("a");
        referLink.href = "profile.html";
        document.body.appendChild(referLink);
        referLink.click();
      }
      else { window.location.replace("profile.html");} 
    } else {
      $scope.waiting = "Ready";
      $scope.heading = "";
      $scope.message = "";
      $scope.submessage = "";
    }
  }
  
  $scope.get_notification = function() {
    $scope.AllNotificationResource = $resource('http://:remote_url/get/notification',
    {"remote_url":$scope.remote_url}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Loading";   
    $scope.AllNotificationResource.get(function(response) { 
        $scope.notifications = response;
        if ($scope.notifications.entities !== undefined) {
          if ($scope.notifications.entities.length > 0) {
            $scope.notify_icon = "icon-list-alt";
            for (var i = 0; i < $scope.notifications.entities.length; i++) {
              if ($scope.notifications.entities[i].n_type === 'GROUPINVITE') {
                $scope.notify = "You have notification(s) that require your attention.";
                $scope.notify_icon = "icon-list-alt icon-white";
                break;
              }
            }
          }
        }
     });  
  }  
    
  $scope.sketch_pagination = {"limit":5, "offset":0, "prev_offset":0, "next_offset":0};
  
  $scope.more_sketch = function() {
    $scope.sketch_pagination = {"limit":5, "offset":0, "prev_offset":0, "next_offset":0};
    $scope.list();
  }
  
  $scope.paginate_back = function() {
    
  }
  
  $scope.paginate_forward = function() {
    if ($scope.sketch_pagination.next_offset > 
        $scope.sketch_pagination.offset) {
      $scope.sketch_pagination.offset = $scope.sketch_pagination.next_offset;
      $scope.list();
    }
  }
  
  $scope.list = function(){
    $scope.listmeta = {};
    $scope.listmeta.data = {'id':$scope.profile_user.id,
                            'show':"latest",
                            "limit":$scope.sketch_pagination.limit,
                            "offset":$scope.sketch_pagination.offset};
    $scope.ListResource = $resource('http://:remote_url/list/sketch/user',
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Loading";
    var listmeta = new $scope.ListResource($scope.listmeta.data);
    listmeta.$save(function(response) {
        $scope.items = response;
        $scope.sketch_pagination.next_offset = $scope.items.next_offset;
        $scope.waiting = "Ready";
    });  
  };
  
/*   $scope.delete_sketch = function(id) {
    var confirm_delete = confirm('Are you sure you want to delete this sketch?');
    if (confirm_delete == true){
      $scope.DeleteSketchResource = $resource('http://:remote_url/delete/sketch/:model_id',
      {"remote_url":$scope.remote_url,"model_id":id}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
      $scope.waiting = "Deleting";
      $scope.DeleteSketchResource.remove(function(response) { 
        var check = response.status
        $scope.list();
        if (check === 'error') {
            $scope.waiting = "Error";
            $scope.heading = "Oops!";
            $scope.message = "Error in deleting sketch.";
            $scope.submessage = "Please try again later.";         
        } else {
            $scope.waiting = "Error";
            $scope.heading = "Sketch Deleted";
            $scope.message = "You have successfully deleted the sketch.";     
        }
      });  
    }
  }; */
  
  $scope.accept = {};
  $scope.accept.data = {'n_id': -1, 'u_g' : -1, 'status': ''};
  
  $scope.notify_accept = function(n_id, u_g) {
    $scope.accept.data.n_id = n_id;
    $scope.accept.data.u_g = u_g;
    $scope.accept.data.status = 'accept';
    $scope.notify_group_action();
  };
  
  $scope.notify_reject = function(n_id, u_g) {
    $scope.accept.data.n_id = n_id;
    $scope.accept.data.u_g = u_g;
    $scope.accept.data.status = 'reject';
    $scope.notify_group_action();
  };
  
  $scope.notify_group_action = function() {
    $scope.NotifyGroupResource = $resource('http://:remote_url/acceptreject/group', 
                  {"remote_url":$scope.remote_url}, 
                  {'save': { method: 'POST',    params: {} }});
 
    $scope.waiting = "Loading";
    var notify_group = new $scope.NotifyGroupResource($scope.accept.data);
    notify_group.$save(function(response) { 
            var result = response;
            $scope.accept.data = {'u_g' : -1, 'status': 'accept'};
            if (result.status === 'success') {
              $scope.waiting = "Error";
              $scope.heading = "Success!";
              $scope.message = result.message;
            } else {
              $scope.waiting = "Error";
              $scope.heading = "Oops...!"
              $scope.message = result.message;
              $scope.submessage = result.submessage;
            }                 
            $scope.get_notification();
            $scope.get_profile();
          }); 
  };
  
  $scope.simpleSearch = function() {
    sharedFunctions.simpleSearch($scope.search);
  }
  
  $scope.getuser();
}