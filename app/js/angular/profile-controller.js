'use strict';

/* Controller for profile.html */

//angular.module('app', ['ngResource']);
function ProfileController($scope,$resource,sharedProperties, sharedFunctions){
    
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
    $scope.currentPage = 1,
        $scope.totalSketches =0
  ,$scope.numPerPage = 5
  ,$scope.maxSize = 5
    ,$scope.dataLoaded=false
    ,$scope.reverse=true
    ,$scope.icon='down'
    ,$scope.sorted_by='created'
    ,$scope.sort_description='Date Created'
    ,$scope.direction_description='Descending';


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
  $scope.selected_search = "Name";
  
  $scope.newgroup = {};
  $scope.newgroup.data = {"group_name":"", "user_id":""};
  
  $scope.test = "-";
  $scope.urltype = "-";
  $scope.profilemeta = {};
  $scope.profilemeta.data = {'id':0};
  
  $scope.editprofilemeta = {};
  $scope.editprofilemeta.data = {'id': 0,
                                 'u_displayname': "",
                                 'contact_updates': false,
                                 'contact_studies': false,
                                 'edit_type': 'self'};
                                 
  
  $scope.reload = false;
  $scope.heading = "";
  $scope.message = "";
  $scope.submessage = "";
  $scope.notify = "You have no new notification(s).";
  $scope.notify_icon = "icon-list-alt";
  
  
  //Search Query Filter
  $scope.query = function(item) {
      return !!((item.data.fileName.indexOf($scope.search || '') !== -1 || item.data.owner.indexOf($scope.search || '') !== -1));
  };

  $scope.predicate_users = '-data.fileName';
  

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
                        {'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                           });  
    $scope.waiting = "Loading";       
    $scope.UserResource.get(function(response) {
          var result = response;
          if (result.u_login === "True" || result.u_login === true) {
            $scope.User = result;
            $scope.User.u_created = $scope.tzformat($scope.User.u_created);
            
            if ($scope.User.u_lastlogin !== "") {
              $scope.User.u_lastlogin = $scope.tzformat($scope.User.u_lastlogin);
            }
            $scope.get_notification();   

          } else {
            $scope.User = {
                          "id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", 
                          "u_login": false, "u_email": "", "g_hash": "", "u_created": "", 
                          "u_lastlogin": "", "u_logincount": "", "u_version": 1.0, 
                          "u_isadmin": false, "u_isactive": false, "is_approved": false,
                          "birth_month": "", "birth_year": "", "parent_email": "",
                          "contact_studies": true, "contact_updates": true
                          };
          }
          
          $scope.determineAccess();
    });
  }

  $scope.determineAccess = function(){
    
    if($scope.User.id > 0)
    {
      if(!$scope.User.is_approved){ window.location.replace("register.html"); }
    }
  }
  
  $scope.setTest = function(test) {
    $scope.test = test;
  }

  $scope.setType = function(type) {
    $scope.urltype = type;
  }
  
  $scope.get_profile = function() {
    var same = (parseInt($scope.test) === parseInt($scope.User.id));
    if ($scope.test === "-") {
      $scope.profile_user = $scope.User;
      $scope.grouplist();
      $scope.list();
      $scope.profile_meta();
      $scope.belong = true;
    } else if (same === true) {
      $scope.profile_user = $scope.User;
      $scope.grouplist();
      $scope.list();
      $scope.profile_meta();
      $scope.belong = true;
    
    } else {
      $scope.belong = false;
      $scope.profilemeta.data.id = $scope.test;
      $scope.ProfileUserResource = $resource('http://:remote_url/user/profileuser',
                                 {"remote_url":$scope.remote_url}, 
                                 {'save': {method: 'POST', params:{} }});
      $scope.waiting = "Loading";       
      var profilemeta = new $scope.ProfileUserResource($scope.profilemeta.data);
      profilemeta.$save(function(response) {
            var result = response;
            if (result.status === "success") {
              $scope.profile_user = result;
              $scope.list();
              $scope.grouplist();
              $scope.profile_meta();
            } else {
              
              if($scope.urltype == "parent")
              {
                //if this is a parent, then show profile to parent
                $scope.get_profile_for_parent();
              }
              else
              {
                window.location.replace("index.html");
              }
            }            
      });
    }
  }

  $scope.get_profile_for_parent = function(){
    $scope.belong = true;
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
      
      if (result.status === "success") {
        $scope.User = result;
        $scope.list();
        $scope.grouplist();
        $scope.profile_meta();
      }
      else{ window.location.replace('index.html');}
    });
  }
  
  $scope.profile_meta = function() {
  
    $scope.editprofilemeta.data = {'id': $scope.profile_user.id,
                                    'u_displayname': $scope.profile_user.u_name,
                                    'contact_updates': $scope.profile_user.contact_updates,
                                    'contact_studies': $scope.profile_user.contact_studies,
                                    'edit_type': 'self'};
  }

  $scope.change_profile = function() {
    if ($scope.belong === true) {
      if ($scope.editprofilemeta.data.u_displayname != $scope.profile_user.u_name
        || $scope.editprofilemeta.data.contact_updates != $scope.profile_user.contact_updates
        || $scope.editprofilemeta.data.contact_studies != $scope.profile_user.contact_studies) {
        bootbox.confirm("Do you really wish to change your profile data?", function(changeAlert) {
          if (changeAlert === true) {
            $scope.edit_profile($scope.editprofilemeta.data);
          } else {
            $scope.editprofilemeta.data = {'id': $scope.profile_user.id,
                                           'u_displayname': $scope.profile_user.u_name,
                                           'contact_updates': $scope.profile_user.contact_updates,
                                           'contact_studies': $scope.profile_user.contact_studies,
                                           'edit_type': 'self'};
          }
        });
      }
    } else {
      $scope.waiting = "Error";
      $scope.heading = "Oops...!";
      $scope.message = "You are not allowed to edit this profile.";
    }
  }
  
  $scope.edit_profile = function(meta) {
    if ($scope.belong === true) {
      if($scope.urltype == "parent"){
        meta['edit_type'] = "parentApproval"
      }

      $scope.EditUserResource = $resource('http://:remote_url/user/edituser',
                                {'remote_url':$scope.remote_url}, 
                                {'update': { method: 'PUT', params: {} }});
      var edit_user = new $scope.EditUserResource(meta);
      $scope.waiting = "Loading";
      edit_user.$update(function(response) {
        var result = response;
        if (result.status === 'success') {
          $scope.waiting = "Error";
          $scope.heading = "Success!";
          $scope.message = "You have successfully changed your profile!";
          $scope.reload = true;
        } else {
          $scope.waiting = "Error";
          $scope.heading = "Oops...!";
          $scope.message = result.message;
          $scope.submessage = result.submessage;
        }
      });

    }
  };
  
  $scope.addgroup = function(){
    $scope.newgroup.data.user_id = $scope.User.id;
    $scope.GroupResource = $resource('http://:remote_url/add/group', 
                  {"remote_url":$scope.remote_url}, 
                  {'save': { method: 'POST',    params: {} }});
 
    $scope.waiting = "Saving";
    var newgroup = new $scope.GroupResource($scope.newgroup.data);
    newgroup.$save(function(response) { 
            var result = response;
            $scope.newgroup.data = {"group_name":"", "user_id":""};
            $scope.grouplist();
            if (result.status === 'success') {
              $scope.waiting = "Error";
              $scope.heading = "Success!";
              $scope.message = "You have successfully founded the group '" + result.g_name + "'!";
            } else {
              $scope.waiting = "Error";
              $scope.heading = "Oops...!"
              $scope.message = result.message;
              $scope.submessage = result.submessage;
            }
          }); 
  };
  
  //To add key/value pairs when creating new objects
  $scope.add_key_to_item = function(){
    $scope.item.data[$scope.newItemKey] = $scope.newItemValue;
    $scope.newItemKey = "";
    $scope.newItemValue = "";
  };    
  
  $scope.grouplist = function() {
    $scope.groupmeta = {};
    $scope.groupmeta.data = {'id':$scope.profile_user.id};
    $scope.GroupListResource = $resource('http://:remote_url/list/group',
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Loading";  
    var groupmeta = new $scope.GroupListResource($scope.groupmeta.data);
    groupmeta.$save(function(response) {
        $scope.groups = response;
     });  
  }

  $scope.acknowledge = function() {
    if ($scope.reload === true) {
      var redirectLink = "profile.html";

      if ($scope.urltype == "parent"){
        redirectLink = "profile.html?id="+ $scope.profile_user.id + "&type=parent";
      }
      
      if(navigator.userAgent.match(/MSIE\s(?!9.0)/))
      {
        var referLink = document.createElement("a");
        referLink.href = redirectLink;
        document.body.appendChild(referLink);
        referLink.click();
      }
      else { window.location.replace(redirectLink); } 
    
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
    
  $scope.sketch_pagination = {"limit":$scope.numPerPage, "offset":0, "prev_offset":0, "next_offset":0,"sortBy":"-"+$scope.sorted_by};

  $scope.more_sketch = function() {
    $scope.sketch_pagination = {"limit":$scope.numPerPage, "offset":0, "prev_offset":0, "next_offset":0,"sortBy":$scope.sorted_by};
    $scope.list();
  }
  
  $scope.paginate_back = function() {

      $scope.sketch_pagination.offset = $scope.sketch_pagination.offset - $scope.numPerPage;
      if( $scope.sketch_pagination.offset <0)
       $scope.sketch_pagination.offset=0;
        $scope.currentPage =$scope.currentPage - 1;
      $scope.list();

  }
  
  $scope.paginate_forward = function() {
    if ($scope.sketch_pagination.next_offset > 
        $scope.sketch_pagination.offset) {
      $scope.sketch_pagination.offset = $scope.sketch_pagination.next_offset;
        $scope.currentPage =$scope.currentPage + 1;
      $scope.list();
    }
  }
  
  $scope.list = function(){
    $scope.listmeta = {};
    $scope.listmeta.data = {'id':$scope.profile_user.id,
                            'urltype': $scope.urltype,
                            'show':"latest",
                            "limit":$scope.sketch_pagination.limit,
                            "offset":$scope.sketch_pagination.offset,
                            "sort":$scope.sketch_pagination.sortBy};
    $scope.ListResource = $resource('http://:remote_url/list/sketch/user',
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Loading";
    var listmeta = new $scope.ListResource($scope.listmeta.data);
    listmeta.$save(function(response) {
        $scope.dataLoaded = true;
        $scope.items = response;
        $scope.sketch_pagination.next_offset = $scope.items.next_offset;
        $scope.totalSketches = $scope.items.count;
        $scope.waiting = "Ready";
    });  
  };
  
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
            $scope.get_profile();
          }); 
  };

  $scope.notification = function() {
    var redirectLink = "notifications.html";
    
    if($scope.urltype == "parent" && $scope.test != "-") {
      var redirectLink = "notifications.html?id=" + $scope.profile_user.id + "&type=parent";  
    }

    window.location.replace(redirectLink);
  }

  $scope.group = function(gid) {
    var redirectLink = "groups.html?id=" + gid;

    if($scope.urltype == "parent" && $scope.test != "-") {
      var redirectLink = "groups.html?id=" + gid + "&type=parent";  
    }

    window.location.replace(redirectLink);
  }

  $scope.view_sketch = function(sid) {
    var redirectLink = "view.html?id=" + sid;

    if($scope.urltype == "parent" && $scope.test != "-") {
      var redirectLink = "view.html?id=" + sid + "&type=parent&uid=" + $scope.profile_user.id ;  
    }

    window.location.replace(redirectLink);
  }
  
  $scope.simpleSearch = function() {
    sharedFunctions.simpleSearch($scope.search);
  }

  $scope.cancel = function () {
    window.location.replace("profile_delete.html?type=disapprove&id=" + $scope.profile_user.id);
  };
  
  $scope.year;
  $scope.setFooterYear = function()
  {
    var today = new Date(),
        today_year = today.getFullYear();

    $scope.year = today_year;
  }

    $scope.orderSketches = function(predicate, reverse) {
         $scope.sorted_by=predicate;
    if($scope.reverse) {
        $scope.icon='down';
            $scope.sketch_pagination = {"limit":$scope.numPerPage, "offset":0, "prev_offset":0, "next_offset":0,"sortBy":"-"+$scope.sorted_by};
    }
    else{
         $scope.sketch_pagination = {"limit":$scope.numPerPage, "offset":0, "prev_offset":0, "next_offset":0,"sortBy":$scope.sorted_by};
        $scope.icon='up';
    }

                   $scope.sketch_pagination.offset=0;
        $scope.currentPage =1;
        $scope.list();
  };
    $scope.reorderSketches = function() {

    if($scope.reverse) {

            $scope.sketch_pagination = {"limit":$scope.numPerPage, "offset":0, "prev_offset":0, "next_offset":0,"sortBy":"-"+$scope.sorted_by};
    }
    else{
         $scope.sketch_pagination = {"limit":$scope.numPerPage, "offset":0, "prev_offset":0, "next_offset":0,"sortBy":$scope.sorted_by};

    }

                   $scope.sketch_pagination.offset=0;
        $scope.currentPage =1;
        $scope.list();
  };
    $scope.numPages = function() {
       try {
           return Math.ceil($scope.totalSketches/ $scope.numPerPage);
       }catch(err) {
           return 0;
       }
    }
    $scope.$watch('numPerPage', function() {

        if($scope.dataLoaded) {
             $scope.sketch_pagination = {"limit":$scope.numPerPage, "offset":0, "prev_offset":0, "next_offset":0,"sortBy":$scope.sorted_by};
                   $scope.sketch_pagination.offset=0;
        $scope.currentPage =1;
        $scope.list();
        }
  },true);

  $scope.setFooterYear();
  $scope.getuser();
}