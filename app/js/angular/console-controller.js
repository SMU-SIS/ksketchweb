'use strict';

/* Controller for profile.html */

//angular.module('app', ['ngResource']);
function ConsoleController($scope,$resource){
    
	$scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "", 'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};

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
  $scope.searchUser = "";
  $scope.selecteduser = "";
  $scope.usersfound = "";
  
  $scope.derp = "derp";
  $scope.newgroup = {};
  $scope.newgroup.data = {"group_name":"", "user_id":""};
  
  
  //Search Query Filter
  $scope.query = function(item) {
      return !!((item.data.fileName.indexOf($scope.search || '') !== -1 || item.data.owner.indexOf($scope.search || '') !== -1));
  };

  //Original Sketch Filter
  $scope.isoriginal = function(files) {
    return (files.data.original === 'original');
  }
  $scope.isnotoriginal = function(files) {
    return (files.data.original !== 'original');
  }

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
    $scope.EditUserResource = $resource('http://:remote_url/edituser',
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
          if ((result.u_login === "True" || result.u_login === true)
              && (result.u_isadmin === "True" || result.u_isadmin === true)) {
            $scope.User = result;
            $scope.alluserlist();
            $scope.versionlist();
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
  }	
  
  $scope.retrieveuser = function(){
    if ($scope.selecteduser !== "" && typeof $scope.selecteduser !== 'undefined') {
      $scope.RetrieveUserResource = $resource('http://:remote_url/user/getuser/:id',
                          {'remote_url':$scope.remote_url, 'id':$scope.selecteduser},
                          {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                             });  
      $scope.waiting = "Updating";       
      $scope.RetrieveUserResource.get(function(response) {
            var result = response;
            if (result.status === "success") {
              $scope.selecteduserdata = result;
              $scope.selecteduserdata.u_created = $scope.tzformat($scope.selecteduserdata.u_created);
              if ($scope.selecteduserdata.u_lastlogin !== "") {
                $scope.selecteduserdata.u_lastlogin = $scope.tzformat($scope.selecteduserdata.u_lastlogin);
              }
              $scope.list();
            }
            $scope.waiting = "Ready";
      });
    }    
  };	
  
  $scope.addgroup = function(){
    $scope.newgroup.data.user_id = $scope.User.id;
    $scope.GroupResource = $resource('http://:remote_url/group', 
                  {"remote_url":$scope.remote_url}, 
                  {'save': { method: 'POST',    params: {} }});
 
    $scope.waiting = "Loading";
    var newgroup = new $scope.GroupResource($scope.newgroup.data);
    newgroup.$save(function(response) { 
            var result = response;
            $scope.newgroup.data = {"group_name":"", "user_id":""};
            $scope.grouplist();
            $scope.waiting = "Ready";
          }); 
  };
  
  //To add key/value pairs when creating new objects
  $scope.add_key_to_item = function(){
    $scope.item.data[$scope.newItemKey] = $scope.newItemValue;
    $scope.newItemKey = "";
    $scope.newItemValue = "";
  };    

  $scope.userlist = function() {
    $scope.selecteduser = "";
    $scope.selecteduserdata = "";
    $scope.items = "";
    $scope.UserListResource = $resource('http://:remote_url/user/listuser/:criteria',
    {"remote_url":$scope.remote_url,"criteria":$scope.searchUser}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";
    $scope.UserListResource.get(function(response) { 
        var result = response;
        if (result.status === "success") {
          $scope.usersfound = result;
        }
        $scope.waiting = "Ready";
     });  
  }
  
  $scope.alluserlist = function() {
    $scope.AllUserListResource = $resource('http://:remote_url/user/listuser',
    {"remote_url":$scope.remote_url}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";
    $scope.AllUserListResource.get(function(response) { 
        var result = response;
        if (result.status === "success") {
          $scope.allusersfound = result;
        }
        $scope.waiting = "Ready";
     });  
  }  
  
  $scope.groupedusers = [];
  //$scope.group_leader = "";
  
  $scope.verify = function() {
    return ($scope.group_leader.id > 0);
  }
  
  $scope.adduser = function(user) {
    if (user.id !== -1) {
      $scope.groupedusers.push(user);
      var index=$scope.allusersfound.entities.indexOf(user);
      $scope.allusersfound.entities.splice(index,1);     
    }
  }
  
  $scope.removeuser = function(user) {
    if (user.id !== -1) {
      $scope.allusersfound.entities.push(user);
      var index=$scope.groupedusers.indexOf(user);
      $scope.groupedusers.splice(index,1); 
    }
  }
  
  $scope.versionlist = function() {
    $scope.VersionResource = $resource('http://:remote_url/list/version',
    {"remote_url":$scope.remote_url}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";
    $scope.VersionResource.get(function(response) { 
        var result = response;
        if (result.status === "success") {
          $scope.versionsfound = result;
        }
        $scope.waiting = "Ready";
     });  
  }
  
  $scope.grouplist = function() {
    $scope.GroupListResource = $resource('http://:remote_url/list/group/:criteria',
    {"remote_url":$scope.remote_url,"criteria":$scope.User.id}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";
    $scope.GroupListResource.get(function(response) { 
        $scope.groups = response;
        $scope.waiting = "Ready";
     });  
  }

  
  $scope.list = function(){
    $scope.ListResource = $resource('http://:remote_url/list/sketch/user/:criteria',
    {"remote_url":$scope.remote_url,"criteria":$scope.selecteduserdata.id}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";
    $scope.ListResource.get(function(response) { 
        $scope.items = response;
        $scope.waiting = "Ready";
     });  
  };
  
  $scope.getuser();
}