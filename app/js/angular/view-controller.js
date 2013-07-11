'use strict';

/* Controller for sketch.html */

//angular.module('app', ['ngResource']);
function ViewController($scope,$resource){

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
  $scope.sketchId = "";  //Placeholder value for sketchId (identifies all sub-versions of the same sketch)
  $scope.version = "";  //Placeholder value for version (identifies version of sketch - starts at "1" unless existing sketch is loaded).
  $scope.fileData = "";  //Placeholder value for fileData (saved data)
  $scope.fileName = "";  //Placeholder value for fileName (name file is saved under)
  $scope.changeDescription = ""; //Placeholder value for changeDescription (change description for file edits)
  $scope.test = -1;
  $scope.version = -1;
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
	$scope.item.data = {"sketchId":"", "version":"", "original":"", "owner":"", "owner_id":"", "fileName":"", "fileData":"", "changeDescription":"", "appver":""};    
          
    
  $scope.setTest = function(test) {
    $scope.test = test;
  }

    
  $scope.setVersion = function(version) {
    $scope.version = version;
  }
  
  
	$scope.setData = function(fileData) {
		$scope.fileData = fileData;
	}
	

/*
	General Add/List (pass "model" to m_type)
*/
  
  
  $scope.get_sketch = function() {
    $scope.getSketch = $resource('http://:remote_url/get/sketch/version/:id/:version', 
             {"remote_url":$scope.remote_url,"id":$scope.test,"version":$scope.version}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";   
    $scope.getSketch.get(function(response) {
        var check = response.success
        if (check !== "no") {
          $scope.item = response;
          $scope.fileData = $scope.item.data.fileData;
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
          if (response.id === "Forbidden") {
            $scope.waiting = "Error";
            $scope.heading = "Access Denied";
            $scope.message = "You have not been granted permission to view this sketch.";
          } else {
            $scope.waiting = "Error";
            $scope.heading = "Oops...!";
            $scope.message = "We're sorry, but the sketch you wanted does not exist.";
            $scope.submessage = "Perhaps the URL that you entered was broken?";
          }
        }
      });  
  }
  
  $scope.acknowledge = function() {
    $scope.waiting = "Ready";
    $scope.heading = "";
    $scope.message = "";
    $scope.submessage = "";
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