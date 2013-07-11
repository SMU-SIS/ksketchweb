'use strict';

/* Controller for profile.html */

//angular.module('app', ['ngResource']);
function ProfileController($scope,$resource){
    
	$scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "", 'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};
  
  $scope.profile_user = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "g_hash": "", 'u_isadmin': false, 'u_isactive': false};
    
  $scope.backend_locations = [
    {url : 'ksketchweb.appspot.com', urlName : 'remote backend' },       
    {url : 'localhost:8080', urlName : 'localhost' } ];

  $scope.showdetails = false;
  
  //Date (Time Zone) Format
  $scope.tzformat = function(utc_date) {
  
    var d = moment(utc_date, "DD MMM YYYY HH:mm:ss");
    return d.format("dddd, Do MMM YYYY, hh:mm:ss");
  };
  
  $scope.search = "";
  $scope.derp = "derp";
  $scope.newgroup = {};
  $scope.newgroup.data = {"group_name":"", "user_id":""};
  $scope.test = "-";
  $scope.heading = "";
  $scope.message = "";
  $scope.submessage = "";
  
  
  //Search Query Filter
  $scope.query = function(item) {
      return !!((item.data.fileName.indexOf($scope.search || '') !== -1 || item.data.owner.indexOf($scope.search || '') !== -1));
  };

  $scope.predicate_users = '-data.fileName';
  

  //Replace this url with your final URL from the SingPath API path. 
  //$scope.remote_url = "localhost:8080";
  $scope.remote_url = "ksketchweb.appspot.com";
  $scope.waiting = "Ready";
  
  //resource calls are defined here

  $scope.Model = $resource('http://:remote_url/:model_type/:id',
                          {},{'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                             }
                      );
  
  /*$scope.edituser = function() {
    $scope.EditUserResource = $resource('http://:remote_url/user/edituser',
                              {'remote_url':$scope.remote_url}, 
                              {'update': { method: 'PUT', params: {} }});
    var edit_user = new $scope.EditUserResource($scope.User);
    $scope.waiting = "Loading";
    edit_user.$update(function(response) {
          $scope.User = response;
          
        });
  };*/
  
  $scope.getuser = function(){
    $scope.UserResource = $resource('http://:remote_url/user/getuser',
                        {'remote_url':$scope.remote_url},
                        {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                           });  
    $scope.waiting = "Updating";       
    $scope.UserResource.get(function(response) {
          var result = response;
          $scope.iiii = result.u_login;
          if (result.u_login === "True" || result.u_login === true) {
            $scope.User = result;
            $scope.User.u_created = $scope.tzformat($scope.User.u_created);
            
            if ($scope.User.u_lastlogin !== "") {
              $scope.User.u_lastlogin = $scope.tzformat($scope.User.u_lastlogin);
            }
          } else {
            $scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "",  'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};
            if (navigator.userAgent.match(/MSIE\s(?!9.0)/))
            {
              var referLink = document.createElement("a");
              referLink.href = "index.html";
              document.body.appendChild(referLink);
              referLink.click();
            }
            else { window.location.replace("index.html");}
          }
          $scope.waiting = "Ready";
    });
  };	
  
  $scope.setTest = function(test) {
    $scope.test = test;
  }
  
  $scope.get_profile = function() {
    if ($scope.test === "-") {
      $scope.profile_user = $scope.User;
      $scope.grouplist();
      $scope.list();
      $scope.belong = true;
    } else if (parseInt($scope.test, 10) === parseInt($scope.User.id, 10)) {
      $scope.profile_user = $scope.User;
      $scope.grouplist();
      $scope.list();
      $scope.belong = true;
    
    } else {
      $scope.belong = false;
      $scope.ProfileUserResource = $resource('http://:remote_url/user/profileuser/:id',
                          {'remote_url':$scope.remote_url, 'id':$scope.test},
                          {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                             });  
      $scope.waiting = "Updating";       
      $scope.ProfileUserResource.get(function(response) {
            var result = response;
            if (result.status === "success") {
              $scope.profile_user = result;
              $scope.list();
              $scope.grouplist();
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
            $scope.waiting = "Ready";
      });
    }
  }
  
  $scope.addgroup = function(){
    $scope.newgroup.data.user_id = $scope.User.id;
    $scope.GroupResource = $resource('http://:remote_url/group', 
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
    $scope.GroupListResource = $resource('http://:remote_url/list/group/:criteria',
    {"remote_url":$scope.remote_url,"criteria":$scope.profile_user.id}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";
    $scope.GroupListResource.get(function(response) { 
        $scope.groups = response;
     });  
  }

  $scope.acknowledge = function() {
    $scope.waiting = "Ready";
    $scope.heading = "";
    $scope.message = "";
    $scope.submessage = "";
  }
  $scope.list = function(){
    $scope.ListResource = $resource('http://:remote_url/list/sketch/user/:criteria',
    {"remote_url":$scope.remote_url,"criteria":$scope.profile_user.id}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";
    $scope.ListResource.get(function(response) { 
        $scope.items = response;
        $scope.waiting = "Ready";
     });  
  };
  
  
  $scope.simpleSearch = function() {
    if ($scope.search.replace(/^\s+|\s+$/g,'') !== "") {
      var searchUrl = "search.html?query=" + $scope.search.replace(/^\s+|\s+$/g,'');
      window.location.href=searchUrl;
    }
  }
  
  $scope.getuser();
}