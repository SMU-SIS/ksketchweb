'use strict';

/* Controller for profile.html */

//angular.module('app', ['ngResource']);
function ProfileDeleteController($scope,$resource,sharedProperties, sharedFunctions){
    
  $scope.User = {
                "id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", 
                "u_login": false, "u_email": "", "g_hash": "", "u_created": "", 
                "u_lastlogin": "", "u_logincount": "", "u_version": 1.0, 
                "u_isadmin": false, "u_isactive": false, "is_approved": false,
                "birth_day": "", "birth_month": "", "birth_year": "",
                "parent_email": "", "contact_studies": true, "contact_updates": true
                };

  $scope.profile_user = {
                        "id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", 
                        "u_login": false, "u_email": "", "g_hash": "", "u_created": "", 
                        "u_lastlogin": "", "u_logincount": "", "u_version": 1.0, 
                        "u_isadmin": false, "u_isactive": false, "is_approved": false,
                        "birth_day": "", "birth_month": "", "birth_year": "",
                        "parent_email": "", "contact_studies": true, "contact_updates": true
                        };

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
  $scope.remote_url = sharedProperties.getBackendUrl();
  $scope.janrain_ref = sharedProperties.getJanrainAccount();
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
          }
    });
  }
  
  $scope.setTest = function(test) {
    $scope.test = test;
  }
  
  $scope.get_profile = function() {
    var same = (parseInt($scope.test) === parseInt($scope.User.id));
    if (same === true) {
      $scope.waiting = "Ready"; 
      $scope.profile_user = $scope.User;
      $scope.profile_meta();
      $scope.belong = true;
    
    } else {
      $scope.belong = false;
      $scope.profilemeta.data.id = $scope.test;
      $scope.ProfileUserResource = $resource('http://:remote_url/user/profileuser2',
                                 {"remote_url":$scope.remote_url}, 
                                 {'save': {method: 'POST', params:{} }});
      $scope.waiting = "Loading";       
      var profilemeta = new $scope.ProfileUserResource($scope.profilemeta.data);
      profilemeta.$save(function(response) {
        $scope.waiting = "Ready";  
        var result = response;
        $scope.profile_user = result;
        $scope.profile_meta();     
      });
    }
  }
  
  $scope.profile_meta = function() {
  
    $scope.editprofilemeta.data = {'id': $scope.profile_user.id,
                                 'u_displayname': $scope.profile_user.u_name,
                                 'u_realname': $scope.profile_user.u_realname};
  }

  $scope.delete = function(){
    $scope.delete_profile($scope.editprofilemeta.data);
  }

  $scope.delete_profile = function(meta) {
    $scope.DeleteUserResource = $resource('http://:remote_url/user/deleteuser',
                              {'remote_url':$scope.remote_url}, 
                              {'update': { method: 'PUT', params: {} }});
    var delete_user = new $scope.DeleteUserResource(meta);
    $scope.waiting = "Loading";
    delete_user.$update(function(response) {
          var result = response;
          if (result.status === 'success') {
            $scope.waiting = "Error";
            $scope.heading = "Success!";
            $scope.message = result.message;//"You have successfully deleted this profile!";
            $scope.reload = true;
          } else {
            $scope.waiting = "Error";
            $scope.heading = "Oops...!";
            $scope.message = result.message;
            $scope.submessage = result.submessage;
          }
    });
  };

  $scope.cancel = function(){
    window.location.replace("index.html");
  }

  $scope.logout = function(){
    window.location.replace("http://ksketchweb.appspot.com/user/logout");
  }

  $scope.getuser();
}