'use strict';

/* Controller for sketch.html */

//angular.module('app', ['ngResource']);
function ApprovalController($scope,$resource,sharedProperties,sharedFunctions){

  $scope.User = {
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

  //Date (Time Zone) Format
  $scope.tzformat = function(utc_date) {
    var d = moment(utc_date, "DD MMM YYYY HH:mm:ss");
    return d.format("dddd, Do MMM YYYY, hh:mm:ss");
  };

  //Replace this url with your final URL from the SingPath API path. 
  //$scope.remote_url = "localhost:8080";
  $scope.remote_url = sharedProperties.getBackendUrl();
  $scope.janrain_ref = sharedProperties.getJanrainAccount();
  $scope.waiting = "Ready";
  $scope.reload = false;
  
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
          $scope.waiting = "Ready";
          if (result.u_login) 
          { 
            $scope.User = result;
            $scope.determineAccess();
          } 
          else { window.location.replace('index.html'); }
    });
  }
  
  //variables and method concerning approval process
  $scope.mark
  $scope.agree;
  $scope.message;
  $scope.editprofilemeta = {};
  $scope.edit_redirect = "";

  $scope.cancel = function () {
    //don't need to update is_approved status
    //logout
    //redirect to index.html
    window.location.replace("/user/logout");
  };

  $scope.agree = function() {
    if($scope.mark)
    {
      //update is_approved status to true
      //redirect to profile.html
      $scope.editprofilemeta.data = {
                                        'id': $scope.User.id,
                                        'u_displayname': $scope.User.u_name,
                                        'u_realname': $scope.User.u_realname,
                                        'is_approved': true};
      $scope.edit_redirect = "agree";
      $scope.edit_profile($scope.editprofilemeta.data);
    }
    else
    {
      //return error message to check agreement
      $scope.waiting = "Error";
      $scope.heading = "Oops...";
      $scope.message = "Please mark the checkbox in order to proceed.";
      $scope.submessage = "";
    }
  }

  $scope.edit_profile = function(meta) {
    $scope.EditUserResource = $resource('http://:remote_url/user/edituser',
                                {'remote_url':$scope.remote_url}, 
                                {'update': { method: 'PUT', params: {} }});
    var edit_user = new $scope.EditUserResource(meta);
    $scope.waiting = "Loading";
    edit_user.$update(function(response) {
          var result = response;
          $scope.waiting = "Ready";
          if($scope.edit_redirect == "agree"){ window.location.replace("profile.html");}
    });
  };

  $scope.acknowledge = function() {
    if ($scope.reload === true) {
      if (navigator.userAgent.match(/MSIE\s(?!9.0)/))
      {
        var referLink = document.createElement("a");
        referLink.href = "approval.html";
        document.body.appendChild(referLink);
        referLink.click();
      }
      else { window.location.replace("approval.html");} 
    } else {
      $scope.waiting = "Ready";
      $scope.heading = "";
      $scope.message = "";
      $scope.submessage = "";
    }
  }

  $scope.determineAccess = function() 
  {
    if ($scope.User.is_approved)
    { window.location.replace("profile.html"); }
    else
    {
      if($scope.User.birth_day != 0 && $scope.User.birth_month != 0 && $scope.User.birth_year != 0)
      {
        if($scope.User.parent_email != "" && $scope.User.parent_email != "not required") 
          { window.location.replace("pending.html");}
        else if($scope.User.parent_email == "") 
          { window.location.replace("register.html");}
      }
      else {window.location.replace("register.html");}
    }
  }

  $scope.getuser();
}