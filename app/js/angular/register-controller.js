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
  
  //variables and method concerning birth date registration
  $scope.selectedDay;
  $scope.selectedMonth;
  $scope.selectedYear;
  $scope.parentEmail;
  $scope.validEmail;
  $scope.message;
  $scope.editprofilemeta = {};
  $scope.edit_redirect = "";
  $scope.parentalConsent = false;
  
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
                                    'birth_day': parseInt(birthDay.date),
                                    'birth_month': parseInt(birthMonth.id),
                                    'birth_year': parseInt(birthYear)};

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
                                    'birth_day': parseInt(birthDay.date),
                                    'birth_month': parseInt(birthMonth.id),
                                    'birth_year': parseInt(birthYear)};

        $scope.edit_redirect = "parent-email";
        $scope.edit_profile($scope.editprofilemeta.data);
      }
    }
  };

  $scope.addParentEmail = function (parentEmail) {
    $scope.validateEmail(parentEmail);
    if($scope.validEmail)
    {
      //update database with parent's email
      alert(parentEmail);
      $scope.editprofilemeta.data = {
                                    'id': $scope.User.id,
                                    'u_displayname': $scope.User.u_name,
                                    'u_realname': $scope.User.u_realname,
                                    'parent_email': parentEmail + ""};

      $scope.edit_redirect = "pending";
      $scope.edit_profile($scope.editprofilemeta.data);
    }
    else
    {
      //add error message back to the page
      $scope.submessage = "Please enter a valid email address"
      return $scope.submessage;
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
    
          if($scope.edit_redirect == "pending")
          { 
            //send out email to parent's email
            //logout user
            //redirect to pending.html
            window.location.replace("pending.html");
          }

          if($scope.edit_redirect == "parent-email")
          {
            message = " Under 18 applicants require parental consent for participation. Please provide your parent's email address."; 
            $scope.parentalConsent = true;
            return $scope.message = message;
          }
    });
  };

  $scope.determineAccess = function() 
  {
    if ($scope.User.is_approved)
      { window.location.replace("profile.html");}
    else
    {
      if($scope.User.birth_day != 0 && $scope.User.birth_month != 0 && $scope.User.birth_year != 0)
      {
        if($scope.User.parent_email == "not required") { window.location.replace("approval.html"); }
        else if($scope.User.parent_email != "") { window.location.replace("pending.html"); }
        else if($scope.User.parent_email == "")
        {
          var tempDay = {date: $scope.User.birth_day},
              tempMonth = {date: $scope.User.birth_month},
              tempYear = $scope.User.birth_year + "";
          $scope.calcAge(tempDay, tempMonth, tempYear);
        }
        
      }
    }
  }

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

  $scope.getuser();
}