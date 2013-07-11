'use strict';

/* Controller for search.html */

//angular.module('app', ['ngResource']);
function SearchController($scope,$resource){
    
	$scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "",  'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};
  
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
  $scope.predicate_users = '-created';
  
  //Replace this url with your final URL from the SingPath API path. 
  //$scope.remote_url = "localhost:8080";
  $scope.remote_url = "ksketchweb.appspot.com";
  $scope.waiting = "Ready";
  $scope.test = "-";
  
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

  $scope.setTest = function(test) {
    $scope.search = test;
  }
  
  $scope.searchlist = function(){
    $scope.SearchResource = $resource('http://:remote_url/list/sketch/:criteria',
    {"remote_url":$scope.remote_url,"criteria":$scope.search}, 
             {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}});
    $scope.waiting = "Updating";   
    $scope.SearchResource.get(function(response) { 
        $scope.searchitems = response;
        $scope.waiting = "Ready";
    });
  };
  
  $scope.getuser();
}