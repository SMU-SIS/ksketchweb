'use strict';

/* Controller for sketch.html */

//angular.module('app', ['ngResource']);
function RegisterController($scope,$resource,sharedProperties,sharedFunctions){

  $scope.User = {
                "id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", 
                "u_login": false, "u_email": "", "g_hash": "", "u_created": "", 
                "u_lastlogin": "", "u_logincount": "", "u_version": 1.0, 
                "u_isadmin": false, "u_isactive": false, "is_approved": false,
                "birth_day": "", "birth_month": "", "birth_year": "",
                "parent_email": "", "contact_studies": true, "contact_updates": true
                };

  $scope.parentalConsent = false;

  $scope.backend_locations = [{url : sharedProperties.getBackendUrl(), urlName : 'remote backend' },       
                              {url : 'localhost:8080', urlName : 'localhost' }];

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
  
  //resource calls are defined here
  $scope.Model = $resource('http://:remote_url/:model_type/:id',
                          {},{'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}}
                          );

  $scope.getuser = function(){
    $scope.UserResource = $resource('http://:remote_url/user/getuser',
                                    {'remote_url':$scope.remote_url},
                                    {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}}
                                    );  
    $scope.waiting = "Loading";       
    $scope.UserResource.get(function(response) {
          var result = response;
          if (result.u_login === "True" || result.u_login === true) {
            $scope.User = result;
            $scope.get_notification();  
            $scope.grouplist();          
          } else {
            $scope.User = {
                          "id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", 
                          "u_login": false, "u_email": "", "g_hash": "", "u_created": "", 
                          "u_lastlogin": "", "u_logincount": "", "u_version": 1.0, 
                          "u_isadmin": false, "u_isactive": false, "is_approved": false,
                          "birth_day": "", "birth_month": "", "birth_year": "",
                          "parent_email": "", "contact_studies": true, "contact_updates": true
                          };
          }
          $scope.waiting = "Ready";
    });
  }

  $scope.selectedDay;
  $scope.selectedMonth;
  $scope.selectedYear;
  $scope.message;
  
  $scope.days = [{id: 1, date: 1}, {id: 2, date: 2}, {id: 3, date: 3}, {id: 4, date: 4}, {id: 5, date: 5},
                {id: 6, date: 6}, {id: 7, date: 7}, {id: 8, date: 8}, {id: 9, date: 9}, {id: 10, date: 10},
                {id: 11, date: 11}, {id: 12, date: 12}, {id: 13, date: 13}, {id: 14, date: 14}, {id: 15, date: 15},
                {id: 16, date: 16}, {id: 17, date: 17}, {id: 18, date: 18}, {id: 19, date: 19}, {id: 20, date: 20},
                {id: 21, date: 21}, {id: 22, date: 22}, {id: 23, date: 23}, {id: 24, date: 24}, {id: 25, date: 25},
                {id: 26, date: 26}, {id: 27, date: 27}, {id: 28, date: 28}, {id: 29, date: 29}, {id: 30, date: 30}, 
                {id: 31, date: 31}];

  $scope.months = [{id: 1, date: "January"}, {id: 2, date: "February"}, {id: 3, date: "March"}, {id: 4, date: "April"}, 
                  {id: 5, date: "May"}, {id: 6, date: "June"}, {id: 7, date: "July"}, {id: 8, date: "August"}, 
                  {id: 9, date: "September"}, {id: 10, date: "October"}, {id: 11, date: "November"}, 
                  {id: 12, date: "December"}];

  $scope.calcAge = function (birthMonth, birthDay, birthYear) {
    var todayDate = new Date(),
        todayYear = todayDate.getFullYear(),
        todayMonth = todayDate.getMonth(),
        todayDay = todayDate.getDate(),
        age = todayYear - parseInt(birthYear);
    var message = "";

    if (todayMonth < birthMonth.date - 1) { age--; }

    if (birthMonth.date - 1 === todayMonth && todayDay < birthDay.date) { age--; }

    if(age == null) { message = "Please enter a valid year. (e.g. YYYY)"; }
    else if (age >= 18) { window.location.replace("approval.html");} 
    else
    {
      message = "Under 18 applicants require parental consent for participation. Please provide your parent's email address."; 
      $scope.parentalConsent = true;
    }

    return $scope.message = message;
  };
}