'use strict';

/* Controller for sketch.html */

//angular.module('app', ['ngResource']);
function SketchController($scope,$resource){

	$scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "", 'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};

  $scope.backend_locations = [
    {url : 'ksketchweb.appspot.com', urlName : 'remote backend' },       
    {url : 'localhost:8080', urlName : 'localhost' } ];

  $scope.search = "";
  $scope.showdetails = false;
  
  //Date (Time Zone) Format
  $scope.tzformat = function(utc_date) {
  
    var d = moment(utc_date, "DD MMM YYYY HH:mm:ss");
    return d.format("dddd, Do MMM YYYY, hh:mm:ss");
  };
  //Sketch
  $scope.sketchId = "";  //Placeholder value for sketchId (identifies all sub-versions of the same sketch).
  $scope.version = "";  //Placeholder value for version (identifies version of sketch - starts at "1" unless existing sketch is loaded).
  $scope.fileData = "";  //Placeholder value for fileData (saved data).
  $scope.thumbnailData = ""; //Placeholder value for thumbnail data.
  $scope.fileName = "";  //Placeholder value for fileName (name file is saved under).
  $scope.tempFileName = ""; //Temporary placeholder for fileName during saveAs.
  $scope.changeDescription = ""; //Placeholder value for changeDescription (change description for file edits)

  
  $scope.permissions = {"p_view": "Public", "p_view_groups": [], "p_edit": "Public", "p_edit_groups": [], "p_comment": "Public", "p_comment_groups": []};
  
  $scope.changePermissions = function(value) {};
  
  $scope.loaded_id = -1;
  $scope.loaded_version = -1;
  $scope.heading = "";
  $scope.message = "";
  $scope.submessage = "";
  
  //Search Query Filter
  $scope.query = function(item) {
      return !!((item.data.fileName.indexOf($scope.search || '') !== -1 || item.data.owner.indexOf($scope.search || '') !== -1));
  };

  //Replace this url with your final URL from the SingPath API path. 
  //$scope.remote_url = "localhost:8080";
  $scope.remote_url = "ksketchweb.appspot.com";
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
    $scope.waiting = "Updating";       
    $scope.UserResource.get(function(response) {
          var result = response;
          $scope.iiii = result.u_login;
          if (result.u_login === "True" || result.u_login === true) {
            $scope.User = result;            
          } else {
            $scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "",  'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};
          }
          $scope.waiting = "Ready";
    });
  }
  
  $scope.item = {};
	$scope.item.data = {"sketchId":"", "version":"", "original":"", "owner":"", "owner_id":"", "fileName":"", "fileData":"", "changeDescription":"", "appver":"", "p_view": "Self", "p_view_groups": [], "p_edit": "Self", "p_edit_groups": [], "p_comment": "Self", "p_comment_groups": []};    
  
	$scope.saveAs = function() { //Saving new file
	   	
		$scope.fileData = $scope.fileData.replace(/(\r\n|\n|\r)/gm," ");
		
		//$scope.item.data = {"sketchId":"", "version":"", "original":"", "owner":"", "owner_id":"", "fileName":"", "fileData":"", "thumbnailData":"", "changeDescription":"", "appver":"","p_view": "Self", "p_view_groups": [], "p_edit": "Self", "p_edit_groups": [], "p_comment": "Self", "p_comment_groups": []};
		$scope.item.data.sketchId = "";			
		
		$scope.item.data.original = $scope.sketchId + ":" + $scope.version;
		
		$scope.item.data.owner = $scope.User.u_name;
    $scope.item.data.owner_id = $scope.User.id;
		$scope.item.data.fileName = $scope.tempFileName;
		$scope.item.data.fileData = $scope.fileData;
		$scope.item.data.thumbnailData = $scope.thumbnailData;
		$scope.item.data.changeDescription = $scope.changeDescription;
    $scope.item.data.appver = $scope.User.u_version;
    
    $scope.item.data.p_view = $scope.permissions.p_view;
    $scope.item.data.p_view_groups = $scope.permissions.p_view_groups;
    $scope.item.data.p_edit = $scope.permissions.p_edit;
    $scope.item.data.p_edit_groups = $scope.permissions.p_edit_groups;
    $scope.item.data.p_comment = $scope.permissions.p_comment;
    $scope.item.data.p_comment_groups = $scope.permissions.p_comment_groups;
		
	  $scope.setMeta($scope.item.data.sketchId, $scope.item.data.version, $scope.item.data.owner, $scope.item.data.owner_id, $scope.item.data.fileName);
		$scope.changeDescription = "" //Clears placeholder before next load.
		
		$scope.add("sketch");
	}
	
	$scope.save = function() { //Save new version of existing file
		$scope.fileData = $scope.fileData.replace(/(\r\n|\n|\r)/gm," ");
		
		//$scope.item.data = {"sketchId":"", "version":"", "original":"", "owner":"", "owner_id":"", "fileName":"", "fileData":"", "thumbnailData":"", "changeDescription":"", "appver":"","p_view": "Self", "p_view_groups": [], "p_edit": "Self", "p_edit_groups": [], "p_comment": "Self", "p_comment_groups": []};
		$scope.item.data.sketchId = $scope.sketchId;
		$scope.item.data.original = $scope.sketchId + ":" + $scope.version; 
		$scope.item.data.owner = $scope.User.u_name;
    $scope.item.data.owner_id = $scope.User.id;
		$scope.item.data.fileName = $scope.fileName;
		$scope.item.data.fileData = $scope.fileData;
		$scope.item.data.thumbnailData = $scope.thumbnailData;
		$scope.item.data.changeDescription = $scope.changeDescription;
    $scope.item.data.appver = $scope.User.u_version;
    
    $scope.item.data.p_view = $scope.permissions.p_view;
    $scope.item.data.p_view_groups = $scope.permissions.p_view_groups;
    $scope.item.data.p_edit = $scope.permissions.p_edit;
    $scope.item.data.p_edit_groups = $scope.permissions.p_edit_groups;
    $scope.item.data.p_comment = $scope.permissions.p_comment;
    $scope.item.data.p_comment_groups = $scope.permissions.p_comment_groups;
		
	  $scope.setMeta($scope.item.data.sketchId, $scope.item.data.version, $scope.item.data.owner, $scope.item.data.owner_id, $scope.item.data.fileName);
		$scope.changeDescription = "" //Clears placeholder before next load.
		
		$scope.add("sketch");		
	}
   
	$scope.setMeta = function(sketchId, version, owner, owner_id, fileName) {
		$scope.sketchId = sketchId;
		$scope.version = version;
		$scope.owner = owner;
    $scope.owner_id = owner_id
		$scope.fileName = fileName;
	}
	
  $scope.setPermissions = function(view, view_groups, edit, edit_groups, comment, comment_groups) {
    $scope.permissions = {"p_view": view, "p_view_groups": view_groups, "p_edit": edit, "p_edit_groups": edit_groups, "p_comment": comment, "p_comment_groups": comment_groups};
  }
    
  $scope.setTest = function(loaded_id) {
    $scope.loaded_id = loaded_id;
  }

    
  $scope.setVersion = function(version) {
    $scope.version = version;
    $scope.loaded_version = version;
  }
  
  
	$scope.setData = function(fileData) {
		$scope.fileData = fileData;
    if (fileData.indexOf("thumbnail data") != -1) {
      var t_index = fileData.indexOf("thumbnail data");
      var t_start = fileData.indexOf("\"", t_index) + 1;
      var t_end = fileData.indexOf("\"", t_start);
      $scope.thumbnailData = fileData.substring(t_start,t_end);
      $scope.thumbnailData = $scope.thumbnailData.replace(/(\r\n|\n|\r)/gm," ");
      var format = new RegExp('&#xA;', 'g');
      $scope.thumbnailData = $scope.thumbnailData.replace(format,"");
    }
	}
	

/*
	General Add/List (pass "model" to m_type)
*/
  
  $scope.add = function(m_type){
    $scope.SaveResource = $resource('http://:remote_url/:model', 
                  {"remote_url":$scope.remote_url,"model":m_type}, 
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
              //$scope.item.data = {"sketchId":"", "version":"", "original":"", "owner":"", "owner_id":"", "fileName":"", "fileData":"", "changeDescription":"", "appver":"","p_view": "Self", "p_view_groups": [], "p_edit": "Self", "p_edit_groups": [], "p_comment": "Self", "p_comment_groups": []};
            } else {
              //$scope.setMeta("","","","","");
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
  
  $scope.get_sketch = function() {
    $scope.getSketch = $resource('http://:remote_url/get/sketch/version/:id/:version', 
             {"remote_url":$scope.remote_url,"id":$scope.loaded_id,"version":$scope.version}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";   
    $scope.getSketch.get(function(response) {
        var check = response.success
        if (check !== "no") {
          var rsketch = response.data;
          $scope.setMeta(rsketch.sketchId, rsketch.version, rsketch.owner, rsketch.owner_id, rsketch.fileName);
          $scope.setPermissions(rsketch.p_view, rsketch.p_view_groups, rsketch.p_edit, rsketch.p_edit_groups, rsketch.p_comment, rsketch.p_comment_groups);
          $scope.fileData = rsketch.fileData;
          $scope.thumbnailData = rsketch.thumbnailData;
          loadKSketchFile($scope.fileData);
          if (check === "yes") {
            $scope.waiting = "Ready";
          } else if (check === "version"){
            $scope.waiting = "Error";
            $scope.heading = "Hmm...";
            $scope.message = "We couldn't find that version of the sketch you wanted.";
            $scope.submessage = "The latest existing version has been loaded instead.";            
          }
        }
        else {
          $scope.waiting = "Error";
          $scope.heading = "Oops...!";
          $scope.message = "We're sorry, but the sketch you wanted does not exist.";
          $scope.submessage = "Perhaps the URL that you entered was broken?";
        }
      });  
  }
  
  $scope.acknowledge = function() {
    $scope.waiting = "Ready";
    $scope.heading = "";
    $scope.message = "";
    $scope.submessage = "";
  }
  
  $scope.reload_sketch = function() {
    var reloadAlert = confirm("Do you wish to abandon your changes and revert to the saved sketch?");
    if (reloadAlert === true) {
      loadKSketchFile($scope.fileData);
    }
  }
  
  $scope.simpleSearch = function() {
    if ($scope.search.replace(/^\s+|\s+$/g,'') !== "") {
      //var searchAlert = confirm("Warning - Navigating away from this page will remove all your unsaved progress.\n\nDo you wish to continue?");
      //if (searchAlert === true) {
        var searchUrl = "search.html?query=" + $scope.search.replace(/^\s+|\s+$/g,'');
        window.location.href=searchUrl;
      } else {
        $scope.search = "";
      }
    //}
  }
  
  $scope.getuser();
}