'use strict';

/* Controller for index.html */

/*
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
*/

//angular.module('app', ['ngResource']);
function IndexController($scope,$resource,sharedProperties, sharedFunctions){
    
	$scope.User = {
                "id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", 
                "u_login": false, "u_email": "", "g_hash": "", "u_created": "", 
                "u_lastlogin": "", "u_logincount": "", "u_version": 1.0, 
                "u_isadmin": false, "u_isactive": false, "is_approved": false,
                "birth_month": "", "birth_year": "", "parent_email": "",
                "contact_studies": true, "contact_updates": true
                };

  $scope.backend_locations = [
    {url : sharedProperties.getBackendUrl(), urlName : 'remote backend' },       
    {url : 'localhost:8080', urlName : 'localhost' } ];

  $scope.showdetails = false;
  $scope.email = sharedProperties.getKSketchEmail();
  //Date (Time Zone) Format
  $scope.tzformat = function(utc_date) {
    var localTime  = moment.utc(utc_date+" UTC").toDate();
    return moment(localTime).format("dddd, Do MMM YYYY, hh:mm:ss a");
  };

  $scope.search = "";
  $scope.notify = "You have no new notification(s).";
  $scope.notify_icon = "icon-list-alt";
  
  //Replace this url with your final URL from the SingPath API path. 
  //$scope.remote_url = "localhost:8080";
  $scope.remote_url = sharedProperties.getBackendUrl();
  $scope.waiting = "Ready";
  
  //resource calls are defined here
  $scope.Model = $resource('http://:remote_url/:model_type/:id',
                          {},{'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}}
                          );
                          
  $scope.getuser = function(){
    $scope.UserResource = $resource('http://:remote_url/user/getuser',
                        {'remote_url':$scope.remote_url},
                        {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                           });  

    $scope.waiting = "Loading";   
    $scope.UserResource.get(function(response) {
          var result = response;
          if (result.u_login == "True" || result.u_login == true) {
            $scope.User = result;
            $scope.get_notification();   
          } else {
            $scope.User = {
                          "id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", 
                          "u_login": false, "u_email": "", "g_hash": "", "u_created": "", 
                          "u_lastlogin": "", "u_logincount": "", "u_version": 1.0, 
                          "u_isadmin": false, "u_isactive": false, "is_approved": false,
                          "birth_month": "", "birth_year": "", "parent_email": "",
                          "contact_studies": true, "contact_updates": true
                          };
          }
          $scope.waiting = "Ready";
          $scope.determineAccess();
    }
    );
  }
  
  $scope.setData = function(fileData) {
    $scope.fileData = fileData;
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
            $scope.accept.data = {'n_id': -1, 'u_g' : -1, 'status': ''};        
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
          }); 
  };

  $scope.acknowledge = function() {
    $scope.waiting = "Ready";
    $scope.heading = "";
    $scope.message = "";
    $scope.submessage = "";
  }
  
  $scope.simpleSearch = function() {
    sharedFunctions.simpleSearch($scope.search);
  }
  
  $scope.determineAccess = function(){
    if($scope.User.id > 0)
    {
      if(!$scope.User.is_approved){ window.location.replace("register.html"); }
    }
  }

  $scope.year;
  $scope.setFooterYear = function()
  {
    var today = new Date(),
        today_year = today.getFullYear();

    $scope.year = today_year;
  }

  $scope.setFooterYear();
  $scope.getuser();
}