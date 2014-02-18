'use strict';

/* Controller for profile.html */

//angular.module('app', ['ngResource']);
function RegisterCompleteController($scope,$resource,sharedProperties, sharedFunctions){
    
  $scope.User = {
                "id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", 
                "u_login": false, "u_email": "", "g_hash": "", "u_created": "", 
                "u_lastlogin": "", "u_logincount": "", "u_version": 1.0, 
                "u_isadmin": false, "u_isactive": false, "is_approved": false,
                "birth_month": "", "birth_year": "", "parent_email": "",
                "contact_studies": true, "contact_updates": true
                };

  $scope.profile_user = {
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
  
  //Date (Time Zone) Format
  $scope.tzformat = function(utc_date) {
  
    var d = moment(utc_date, "DD MMM YYYY HH:mm:ss");
    return d.format("dddd, Do MMM YYYY, hh:mm:ss");
  };

  $scope.belong = true;
  $scope.test = "-";
  $scope.profilemeta = {};
  $scope.profilemeta.data = {'id':0};
  
  $scope.reload = false;
  $scope.heading = "";
  $scope.message = "";
  $scope.submessage = "";

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
          $scope.waiting = "Ready";  
          if (result.u_login === "True" || result.u_login === true) {
            $scope.User = result;
            $scope.User.u_created = $scope.tzformat($scope.User.u_created);
            
            if ($scope.User.u_lastlogin !== "") {
              $scope.User.u_lastlogin = $scope.tzformat($scope.User.u_lastlogin);
            }            

            $scope.User.parent_email == "not required"
            { $scope.belong = true; }
          }
    });
  }
  
  $scope.setTest = function(test) {
    $scope.test = test;

    if($scope.test != "-")
    { 
      //this action is from a parent approving the registration
      //end it by sending complete registration email
      $scope.sendCompleteEmail();
    }
  }
  
  $scope.get_profile = function() {
    var same = (parseInt($scope.test) === parseInt($scope.User.id));
    if ((same === true) || ($scope.test == "-" && $scope.User.id > 0))
    {
      $scope.waiting = "Ready"; 
      $scope.profile_user = $scope.User;
      $scope.profile_meta();
    } 
    else {
      if($scope.test != "-")
      {
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
          
          if($scope.profile_user.status == "Error")
          { window.location.replace('index.html');}
        });
      }
    }

    $scope.determineAccess();
  }

  $scope.sendCompleteEmail = function()
  {
    $scope.SendResource = $resource('http://:remote_url/user/parentcomplete',
                                   {"remote_url":$scope.remote_url}, 
                                   {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Loading";    

    var data = {};
    data.data = {'id':0};
    data.data.id = $scope.test;   
    var sendmeta = new $scope.SendResource(data.data);
    sendmeta.$save(function(response) {
      var result = response;
      $scope.waiting = "Ready";
    });
  }

  $scope.logout = function(){
    window.location.replace("http://ksketch.smu.edu.sg/user/logout");
  }

  $scope.determineAccess = function() 
  {
    if($scope.test == "-" && $scope.User.id == 0) 
    { window.location.replace('index.html');}
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