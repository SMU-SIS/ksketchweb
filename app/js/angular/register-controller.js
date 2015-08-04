'use strict';

/*
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
*/

/* Controller for sketch.html */

//angular.module('app', ['ngResource']);
function RegisterController($scope,$resource,sharedProperties,sharedFunctions){

  $scope.User = {
                "id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", 
                "u_login": false, "u_email": "", "g_hash": "", "u_created": "", 
                "u_lastlogin": "", "u_logincount": "", "u_version": 1.0, 
                "u_isadmin": false, "u_isactive": false, "is_approved": false,
                "birth_month": 0, "birth_year": 0, "parent_email": "",
                "contact_studies": true, "contact_updates": true
                };

  $scope.backend_locations = [
    {url : sharedProperties.getBackendUrl(), urlName : 'remote backend' },       
    {url : 'localhost:8080', urlName : 'localhost' } ];

  //Date (Time Zone) Format
  $scope.tzformat = function(utc_date) {
    var localTime  = moment.utc(utc_date+" UTC").toDate();
    return moment(localTime).format("dddd, Do MMM YYYY, hh:mm:ss a");
  };

  //Replace this url with your final URL from the SingPath API path. 
  //$scope.remote_url = "localhost:8080";
  $scope.remote_url = sharedProperties.getBackendUrl();
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
  
  //variables and method concerning birth date registration
  $scope.selectedMonth;
  $scope.selectedYear;
  $scope.parentEmail;
  $scope.validEmail;
  $scope.message;
  $scope.parent_message;
  $scope.editprofilemeta = {};
  $scope.edit_redirect = "";
  $scope.parentalConsent = false;

  $scope.months = [{id: 1, date: "January"}, {id: 2, date: "February"}, {id: 3, date: "March"}, {id: 4, date: "April"}, 
                  {id: 5, date: "May"}, {id: 6, date: "June"}, {id: 7, date: "July"}, {id: 8, date: "August"}, 
                  {id: 9, date: "September"}, {id: 10, date: "October"}, {id: 11, date: "November"}, 
                  {id: 12, date: "December"}];

  $scope.calcAge = function (birthMonth, birthYear, type) {
    var todayDate = new Date(),
        todayYear = todayDate.getFullYear(),
        todayMonth = todayDate.getMonth(),
        todayDay = todayDate.getDate(),
        is_valid = false,
        age = 0,
        parent_message = "";

    var isnum = /^\d+$/.test(birthYear);
    if (isnum) { is_valid = true; }

    if (is_valid) 
    { 
      is_valid = false;
      if(todayYear > parseInt(birthYear)) { is_valid = true; }

      if (is_valid) 
      {
        age = todayYear - parseInt(birthYear);
        if (todayMonth < birthMonth.id) 
        { 
          if(age > 1) {age--;}
        }
      }
    }

    if(age == 0 && type != "determineAccess") 
    { 
      $scope.waiting = "Error";
      $scope.heading = "Oops...!";
      $scope.message = "Please enter a valid birth date. (Month - YYYY)";
    }
    else
    {
      if (age >= 18) 
      { 
        //update user's birth day, month and year in database
        //update parent's email to undefined@undefined.com
        $scope.editprofilemeta.data = {
                                    'id': $scope.User.id,
                                    'u_displayname': $scope.User.u_name,
                                    'u_realname': $scope.User.u_realname,
                                    'parent_email': "not required",
                                    'birth_month': parseInt(birthMonth.id),
                                    'birth_year': parseInt(birthYear),
                                    'edit_type': "self"};

        $scope.edit_redirect = "approval";
        $scope.edit_profile($scope.editprofilemeta.data);
      } 
      else if (age < 18)
      {
        //update user's birth day, month and year in database
        $scope.editprofilemeta.data = {
                                    'id': $scope.User.id,
                                    'u_displayname': $scope.User.u_name,
                                    'u_realname': $scope.User.u_realname,
                                    'birth_month': parseInt(birthMonth.id),
                                    'birth_year': parseInt(birthYear),
                                    'edit_type': "self"};

        $scope.edit_profile($scope.editprofilemeta.data);

        parent_message = " Under 18 participants require parental consent. Please provide your parent's email address."; 
        $scope.parentalConsent = true; 
        return $scope.parent_message = parent_message;
      }
    }
    
  };

  $scope.addParentEmail = function (parentEmail) {
    $scope.validateEmail(parentEmail);
    var date_month = 0,
        date_year = 0;

    if($scope.validEmail)
    {
      if(parentEmail != $scope.User.u_email)
      {
        if($scope.selectedMonth)
        {
          date_month = $scope.selectedMonth.id;
          date_year = parseInt($scope.selectedYear);
        }
        else
        {
          date_month = $scope.User.birth_month;
          date_year = $scope.User.birth_year;
        }

        //update database with parent's email
        $scope.editprofilemeta.data = {
                                      'id': $scope.User.id,
                                      'u_displayname': $scope.User.u_name,
                                      'u_realname': $scope.User.u_realname,
                                      'parent_email': parentEmail + "",
                                      'birth_month': date_month,
                                      'birth_year': date_year,
                                      'edit_type': "self"};

        $scope.edit_redirect = "pending";
        $scope.edit_profile($scope.editprofilemeta.data);
      }
      else
      {
        //add error message back to the page
        $scope.waiting = "Error";
        $scope.heading = "Oops...!";
        $scope.message = "Please enter a different email address";
      }
    }
    else
    {
      //add error message back to the page
      $scope.waiting = "Error";
      $scope.heading = "Oops...!";
      $scope.message = "Please enter a valid email address";
    }
  };

  $scope.validateEmail = function(email){
    if (/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(email))  
    {  
      return $scope.validEmail = true;  
    } 
    
    return $scope.validEmail = false;
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

          if($scope.edit_redirect == "approval"){ window.location.replace("approval.html");}
    
          if($scope.edit_redirect == "pending"){ $scope.sendApprovalEmail();}
    });
  };

  $scope.sendApprovalEmail = function()
  {
    $scope.VerifyResource = $resource('http://:remote_url/user/parentapproval',
                        {'remote_url':$scope.remote_url},
                        {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                           });  

    $scope.waiting = "Loading";     
    $scope.VerifyResource.get(function(response) {
          var result = response;
          $scope.waiting = "Ready";
          if (result.status === 'success') 
          { window.location.replace("pending.html");}
    });
  }

  $scope.determineAccess = function() 
  {
    if ($scope.User.is_approved)
      { window.location.replace("profile.html");}
    else
    {
      if($scope.User.birth_month != 0 && $scope.User.birth_year != 0)
      {
        if($scope.User.parent_email == "not required") { window.location.replace("approval.html"); }
        else if($scope.User.parent_email != "") { window.location.replace("pending.html"); }
        else if($scope.User.parent_email == "")
        {
          var tempMonth = {id: $scope.User.birth_month, date: $scope.User.birth_month},
              tempYear = $scope.User.birth_year + "";
          
          $scope.calcAge(tempMonth, tempYear, "determineAccess");
        }
        
      }
    }
  }

  $scope.cancel = function () {
    window.location.replace("profile_delete.html?type=disapprove&id=" + $scope.User.id);
  };

  $scope.acknowledge = function() {
    if ($scope.reload === true) {
      if (navigator.userAgent.match(/MSIE\s(?!9.0)/))
      {
        var referLink = document.createElement("a");
        referLink.href = "register.html";
        document.body.appendChild(referLink);
        referLink.click();
      }
      else { window.location.replace("register.html");} 
    } else {
      $scope.waiting = "Ready";
      $scope.heading = "";
      $scope.message = "";
      $scope.submessage = "";
    }
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