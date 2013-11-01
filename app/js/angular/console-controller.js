'use strict';

/* Controller for profile.html */

//angular.module('app', ['ngResource']);
function ConsoleController($scope,$resource,sharedProperties, sharedFunctions){
    
	$scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "", 'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};

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
  $scope.searchUser = "";
  $scope.selecteduser = "";
  $scope.usersfound = "";
  $scope.test = "-";
  
  $scope.newgroup = {};
  $scope.newgroup.data = {"group_name":"", "user_id":""};
  
  
  //Search Query Filter
  $scope.query = function(item) {
      return !!((item.data.fileName.indexOf($scope.search || '') !== -1 || item.data.owner.indexOf($scope.search || '') !== -1));
  };

  //Original Sketch Filter
  $scope.isoriginal = function(files) {
    return ((files.data.originalSketch === files.data.sketchId)
            && (files.data.originalVersion === files.data.version));
  }
  $scope.isnotoriginal = function(files) {
    return ((files.data.originalSketch != files.data.sketchId)
            || (files.data.originalVersion != files.data.version));
  }

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
    $scope.waiting = "Loading";       
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
    });
  }  
  
  $scope.retrieveuser = function(){
    if ($scope.selecteduser !== undefined) {
      $scope.retrieveusermeta = {};
      $scope.retrieveusermeta.data = {'id':$scope.selecteduser};
      $scope.RetrieveUserResource = $resource('http://:remote_url/user/getuserid',
                      {"remote_url":$scope.remote_url}, 
                      {'save': { method: 'POST',    params: {} }});
   
      $scope.waiting = "Loading";     
      var retrieveusermeta = new $scope.RetrieveUserResource($scope.retrieveusermeta.data);
      retrieveusermeta.$save(function(response) {
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
  }
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
    $scope.selected = "";
    $scope.selecteduser = undefined;
    $scope.selecteduserdata = "";
    $scope.items = "";
    $scope.userlistmeta = {};
    $scope.userlistmeta.data = {'criteria':$scope.searchUser};
    $scope.UserListResource = $resource('http://:remote_url/user/listuser',
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Updating";
    var userlistmeta = new $scope.UserListResource($scope.userlistmeta.data);
    userlistmeta.$save(function(response) {
        var result = response;
        if (result.status === "success") {
          $scope.usersfound = result;
          if ($scope.usersfound.entities.length > 0) {
            $scope.selecteduser = $scope.usersfound.entities[0];
          } else {
            $scope.selected = "No user(s) found!";
          }
        }
        $scope.waiting = "Ready";
     });  
  }
  
  $scope.alluserlist = function() {
    $scope.userlistmeta = {};
    $scope.userlistmeta.data = {'criteria':""};
    $scope.AllUserListResource = $resource('http://:remote_url/user/listuser',
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Updating";
    var userlistmeta = new $scope.AllUserListResource($scope.userlistmeta.data);
    userlistmeta.$save(function(response) {
        var result = response;
        if (result.status === "success") {
          $scope.allusersfound = result;
        }
        $scope.waiting = "Ready";
     });  
  }  
  
  $scope.groupedusers = [];
  $scope.group_leader = {'u_name':"", 'id':0};
  
  $scope.verify = function() {
    if ($scope.group_leader.id > 0 && $scope.new_group.replace(/^\s+|\s+$/g,'') !== "") {
      return true;
    } else {
      return false;
    }
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
  
  $scope.create_group = function (){
    if ($scope.verify() === true) {
      
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

  
  $scope.console_pagination = {"limit":0, "offset":0, "prev_offset":0, "next_offset":0};
  
  $scope.more_sketch = function() {
    $scope.console_pagination = {"limit":5, "offset":0, "prev_offset":0, "next_offset":0};
    $scope.list();
  }
  
  $scope.paginate_back = function() {
    
  }
  
  $scope.paginate_forward = function() {
    if ($scope.console_pagination.next_offset > 
        $scope.console_pagination.offset) {
      $scope.console_pagination.offset = $scope.console_pagination.next_offset;
      $scope.list();
    }
  }
  
  $scope.list = function(){
    $scope.listmeta = {};
    $scope.listmeta.data = {'id':$scope.selecteduserdata.id,
                            'show':"latest",
                            "limit":$scope.console_pagination.limit,
                            "offset":$scope.console_pagination.offset};
    $scope.ListResource = $resource('http://:remote_url/list/sketch/user',
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Loading";
    var listmeta = new $scope.ListResource($scope.listmeta.data);
    listmeta.$save(function(response) {
        $scope.items = response;
        $scope.console_pagination.next_offset = $scope.items.next_offset;
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
  
  $scope.acknowledge = function() {
    $scope.waiting = "Ready";
    $scope.heading = "";
    $scope.message = "";
    $scope.submessage = "";
  }
  $scope.getuser();
}