'use strict';

/* Controller for sketch.html */

//angular.module('app', ['ngResource']);
function SketchController($scope,$resource,sharedProperties,sharedFunctions){

	$scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "", 'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};

  $scope.backend_locations = [
    {url : sharedProperties.getBackendUrl(), urlName : 'remote backend' },       
    {url : 'localhost:8080', urlName : 'localhost' } ];

  $scope.search = "";
  $scope.showdetails = false;

  $scope.editor_location = "swf/v2/KSketch2_Web.swf";
  $scope.get_editor = function() {
    return $scope.editor_location;
  }
  
  
  //Date (Time Zone) Format
  $scope.tzformat = function(utc_date) {
  
    var d = moment(utc_date, "DD MMM YYYY HH:mm:ss");
    return d.format("dddd, Do MMM YYYY, hh:mm:ss");
  };
  //Sketch
  $scope.sketchId = -1;  //Placeholder value for sketchId (identifies all sub-versions of the same sketch).
  $scope.version = -1;  //Placeholder value for version (identifies version of sketch - starts at "1" unless existing sketch is loaded).
  $scope.fileData = "";  //Placeholder value for fileData (saved data).
  $scope.oldThumbnailData = ""; //Placeholder value for old file data.
  $scope.thumbnailData = ""; //Placeholder value for thumbnail data.
  $scope.fileName = "";  //Placeholder value for fileName (name file is saved under).
  $scope.tempFileName = ""; //Temporary placeholder for fileName during saveAs.
  $scope.changeDescription = ""; //Placeholder value for changeDescription (change description for file edits)
  $scope.added = ""; //Notification placeholder if permissions for a group have already been added.


  
  $scope.loaded_id = -1;
  $scope.loaded_version = -1;
  $scope.is_latest = true;
  $scope.heading = "";
  $scope.message = "";
  $scope.submessage = "";
  $scope.notify = "You have no new notification(s).";
  $scope.notify_icon = "icon-list-alt";
  
  //Search Query Filter
  $scope.query = function(item) {
      return !!((item.data.fileName.indexOf($scope.search || '') !== -1 || item.data.owner.indexOf($scope.search || '') !== -1));
  };

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
            $scope.get_notification();  
            $scope.grouplist();           
          } else {
            $scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "",  'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};
          }
          $scope.waiting = "Ready";
    });
  }
  
  $scope.item = {};
	$scope.item.data = {"sketchId":"", "version":"", "originalSketch":-1,"originalVersion":-1, "owner":"", "owner_id":"", "fileName":"", "fileData":"", "changeDescription":"", "appver":"", "p_view": true, "p_edit": true, "p_comment": true, "group_permissions": []};    
  
	$scope.saveAs = function() { //Saving new sketch/saving new sketch as existing sketch
	   	
		$scope.fileData = $scope.fileData.replace(/(\r\n|\n|\r)/gm," ");
		
		$scope.item.data.sketchId = "";			
		
		$scope.item.data.originalSketch = $scope.sketchId;
		$scope.item.data.originalVersion = $scope.version;
		
		$scope.item.data.owner = $scope.User.u_name;
    $scope.item.data.owner_id = $scope.User.id;
		$scope.item.data.fileName = $scope.tempFileName;
		$scope.item.data.fileData = $scope.fileData;
		$scope.item.data.thumbnailData = $scope.thumbnailData;
		$scope.item.data.changeDescription = $scope.changeDescription;
    $scope.item.data.appver = $scope.User.u_version;
    
    $scope.item.data.p_view = $scope.permissions.p_view;
    $scope.item.data.p_edit = $scope.permissions.p_edit;
    $scope.item.data.p_comment = $scope.permissions.p_comment;
    $scope.item.data.group_permissions = $scope.permissions.group_permissions;
		
	  $scope.setMeta($scope.item.data.sketchId, $scope.item.data.version, $scope.item.data.owner, $scope.item.data.owner_id, $scope.item.data.fileName);
		$scope.changeDescription = "" //Clears placeholder before next load.
		
		$scope.add_sketch();
	}
	
	$scope.save = function() { //Save new version of existing file
    if ($scope.allow_save()) {
      $scope.fileData = $scope.fileData.replace(/(\r\n|\n|\r)/gm," ");
      
      $scope.item.data.sketchId = $scope.sketchId;
      
      $scope.item.data.originalSketch = $scope.sketchId;
      $scope.item.data.originalVersion = $scope.version;
      $scope.item.data.owner = $scope.owner;
      $scope.item.data.owner_id = $scope.owner_id;
      $scope.item.data.fileName = $scope.fileName;
      $scope.item.data.fileData = $scope.fileData;
      $scope.item.data.thumbnailData = $scope.thumbnailData;
      $scope.item.data.changeDescription = $scope.changeDescription;
      $scope.item.data.appver = $scope.User.u_version;
      
      $scope.item.data.p_view = $scope.permissions.p_view;
      $scope.item.data.p_edit = $scope.permissions.p_edit;
      $scope.item.data.p_comment = $scope.permissions.p_comment;
      $scope.item.data.group_permissions = $scope.permissions.group_permissions;
      
      $scope.setMeta($scope.item.data.sketchId, $scope.item.data.version, $scope.item.data.owner, $scope.item.data.owner_id, $scope.item.data.fileName);
      $scope.changeDescription = "" //Clears placeholder before next load.
      
      $scope.add_sketch();		
    }
	}
   
	$scope.setMeta = function(sketchId, version, owner, owner_id, fileName) {
		$scope.sketchId = sketchId;
		$scope.version = version;
		$scope.owner = owner;
    $scope.owner_id = owner_id
		$scope.fileName = fileName;
    $scope.tempFileName = fileName;
    $scope.waiting = "Ready";
	}

  $scope.permissions = {"p_view": 1, "p_edit": true, "p_comment": true, "group_permissions": []};
  $scope.group_data = {"edit": false, "comment": false};
  //$scope.group_data.data = undefined;
  
  $scope.changePermissions = function(value) {
    if (value = "changePermissions(1)") {
      $scope.permissions.p_edit = false;
      $scope.permissions.p_comment = false;
    }
  };
  $scope.addgroupperm = function() {
    if ($scope.group_data.data == undefined) return;
    var check_perm = false;
    for (var i = 0; i < $scope.permissions.group_permissions.length; i++) {
      var perm = $scope.permissions.group_permissions[i];
      if ($scope.group_data.id === perm.id) {
        $scope.added = "You have already added permissions for this group!";
        check_perm = true;
        break;
      }
    }
    if (!check_perm) {
      $scope.permissions.group_permissions.push($scope.group_data);
      $scope.group_data = {"edit": false, "comment": false};
      $scope.group_data.data = undefined;
      $scope.added = "";
    }
  }
	
  $scope.removegroupperm = function(id) {
    var index = $scope.permissions.group_permissions.indexOf(id);
    $scope.permissions.group_permissions.splice(index, 1);
    $scope.added = "";
  }
  
  $scope.setPermissions = function(view, edit, comment, group_permissions) {
    $scope.permissions = {"p_view": view, "p_edit": edit, "p_comment": comment, "group_permissions": group_permissions};
  }
    
  $scope.setTest = function(loaded_id) {
    $scope.loaded_id = loaded_id;
  }

    
  $scope.setVersion = function(version) {
    $scope.version = version;
    $scope.loaded_version = version;
  }
  
  
	$scope.setData = function(fileData) {
    $scope.oldThumbnailData = $scope.thumbnailData;
		$scope.fileData = fileData;
    if (fileData.indexOf("thumbnail data") != -1) {
      var t_index = fileData.indexOf("thumbnail data");
      var t_start = fileData.indexOf("\"", t_index) + 1;
      var t_end = fileData.indexOf("\"", t_start);
      $scope.thumbnailData = fileData.substring(t_start,t_end);
      $scope.thumbnailData = $scope.thumbnailData.replace(/(\r\n|\n|\r)/gm," ");
      var format = new RegExp('&#xA;', 'g');
      $scope.thumbnailData = $scope.thumbnailData.replace(format,"");
    } else {
      $scope.thumbnailData = "";
    }
	}
	

  $scope.grouplist = function() {
    if ($scope.User.id != 0) {
      $scope.groupmeta = {};
      $scope.groupmeta.data = {'id':$scope.User.id};
      $scope.GroupListResource = $resource('http://:remote_url/list/group',
               {"remote_url":$scope.remote_url}, 
               {'save': {method: 'POST', params:{} }});
      $scope.waiting = "Loading";  
      var groupmeta = new $scope.GroupListResource($scope.groupmeta.data);
      groupmeta.$save(function(response) {
          $scope.groups = response;
      });  
    }
  }
  
  $scope.add_sketch = function(){
    $scope.added = "";
    $scope.SaveResource = $resource('http://:remote_url/add/sketch', 
                  {"remote_url":$scope.remote_url}, 
                  {'save': { method: 'POST',    params: {} }});
 
    $scope.waiting = "Saving";
    var item = new $scope.SaveResource($scope.item.data);
    item.$save(function(response) { 
            var result = response;
            if (result.status === "success") {
              $scope.waiting = "Error";
              $scope.heading = "Success!";
              $scope.message = "You have successfully saved '" + $scope.fileName + "' (version " + result.data.version + ").";
              $scope.sketchId = result.data.sketchId;
              $scope.setTest(result.data.sketchId);
              $scope.setVersion(result.data.version);
            } else {
              $scope.waiting = "Error";
              $scope.heading = "Oops...!";
              $scope.message = result.message;
            }
          }); 
  };
  
  //To add key/value pairs when creating new objects
  $scope.add_key_to_item = function(){
    $scope.item.data[$scope.newItemKey] = $scope.newItemValue;
    $scope.newItemKey = "";
    $scope.newItemValue = "";
  };    
  
  $scope.allow_save = function() {
    if ($scope.loaded_id !== -1 && $scope.is_latest) {
      return true;
    } else {
      return false;
    }
  }
  
  $scope.get_sketch = function() {
    $scope.sketchmeta = {};
    $scope.sketchmeta.data = {"id":$scope.loaded_id,"version":$scope.version};
    $scope.SketchResource = $resource('http://:remote_url/get/sketch/edit', 
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Loading";      
    var sketchmeta = new $scope.SketchResource($scope.sketchmeta.data);
    sketchmeta.$save(function(response) {
        var check = response.status
        if (check === "Forbidden") {
          $scope.waiting = "Error";
          $scope.heading = "Access Denied";
          $scope.message = "You have not been granted permission to edit this sketch.";
          $scope.leave = true;
        } else if (check === "Error") {
          $scope.waiting = "Error";
          $scope.heading = "Oops...!";
          $scope.message = "We're sorry, but the sketch you wanted does not exist.";
          $scope.submessage = "Perhaps the URL that you entered was broken?";
          $scope.leave = true;
        } else {
          var rsketch = response.data;
          $scope.setMeta(rsketch.sketchId, rsketch.version, rsketch.owner, rsketch.owner_id, rsketch.fileName);
          $scope.setPermissions(rsketch.p_public.p_view, rsketch.p_public.p_edit, rsketch.p_public.p_comment, rsketch.groups);
          $scope.fileData = rsketch.fileData;
          $scope.thumbnailData = rsketch.thumbnailData;
          loadKSketchFile($scope.fileData);
          if (rsketch.ismatching === "False" || rsketch.ismatching === false){
            $scope.waiting = "Error";
            $scope.heading = "Hmm...";
            $scope.message = "We couldn't find that version of the sketch you wanted.";
            $scope.submessage = "The latest existing version has been loaded instead.";            
          } else if (rsketch.islatest === "False" || rsketch.islatest === false){
            $scope.is_latest = false;
            $scope.waiting = "Error";
            $scope.heading = "Hmm...";
            $scope.message = "You have loaded an earlier version of '" + rsketch.fileName + "'.";
            $scope.submessage = "You may not edit this version, but you can save it as a new sketch.";
            
          } else {
            $scope.waiting = "Ready";
          } 
        }
    });  
  }
  
  $scope.acknowledge = function() {
    if ($scope.leave === true) {
      if (navigator.userAgent.match(/MSIE\s(?!9.0)/))
      {
        var referLink = document.createElement("a");
        referLink.href = "index.html";
        document.body.appendChild(referLink);
        referLink.click();
      }
      else { window.location.replace("index.html");} 
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
          }); 
  };
  
  $scope.simpleSearch = function() {
    sharedFunctions.simpleSearch($scope.search);
  }
  
  $scope.getStatus = function() {
    if ($scope.waiting == "Ready") {
      if ($scope.oldThumbnailData !== $scope.thumbnailData) {
        return true;
      } else {
        return false;
      }
    } else {
      return false;
    }
  }
  
  $scope.getuser();
}