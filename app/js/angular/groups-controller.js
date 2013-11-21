'use strict';

/* Controller for groups.html */

//angular.module('app', ['ngResource']);
function GroupsController($scope,$resource,sharedProperties, sharedFunctions){
    
	$scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "",  'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};
    
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
  $scope.predicate_users = '-data.fileName';  
  $scope.derp = "derp";
  $scope.test = "-";
  $scope.belong = false;
  $scope.founder = false;
  $scope.leave = false;
  
  $scope.group_name = "-";
  $scope.u_groups = [];
  $scope.notify = "You have no new notification(s).";
  $scope.notify_icon = "icon-list-alt";
  
  
  //Search Query Filter
  $scope.query = function(item) {
      return !!((item.data.fileName.indexOf($scope.search || '') !== -1 || item.data.owner.indexOf($scope.search || '') !== -1));
  };


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
          if (result.u_login === "True" || result.u_login === true) {
            $scope.User = result;
            $scope.get_notification();             
          } else {
            $scope.User = {"id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User", "u_login": false, "u_email": "", "g_hash": "",  'u_created': "", 'u_lastlogin': "", 'u_logincount': "", 'u_version': 1.0, 'u_isadmin': false, 'u_isactive': false};
            if (navigator.userAgent.match(/MSIE\s(?!9.0)/))
            {
              var referLink = document.createElement("a");
              referLink.href = "index.html";
              document.body.appendChild(referLink);
              referLink.click();
            }
            else { window.location.replace("index.html");}
          }
    });
  }
    
  $scope.groupmeta = {};
  $scope.groupmeta.data = {'id':$scope.test,
                          'criteria': "",
                          'limit': 5,
                          'offset': 0};
  
  $scope.setTest = function(test) {
    $scope.test = test;
    $scope.groupmeta.data.id = $scope.test;
  }
  
  
  $scope.get_group = function() {
    $scope.GroupResource = $resource('http://:remote_url/get/group', 
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Loading";   
    var groupmeta = new $scope.GroupResource($scope.groupmeta.data);
    groupmeta.$save(function(response) {
        var thisgroup = response;
        if (thisgroup.status === "success") {
          $scope.setGroup(thisgroup.group_name, thisgroup.u_groups);
          for (var i = 0; i < thisgroup.u_groups.length; i++) {
            var u_g = thisgroup.u_groups[i]
            if (u_g.user_id === $scope.User.id) {
              if (u_g.role === "Founder") {
                $scope.belong = true;
                $scope.founder = true;
              } else if (u_g.role === "Member") {
                $scope.belong = true;
                $scope.founder = false;
              } else {
                $scope.belong = false;
                $scope.founder = false;
              }
              break;
            }
          }
          $scope.list();
        } else {
          $scope.waiting = "Error";
          $scope.heading = "Oops...!";
          $scope.message = thisgroup.message;
          $scope.submessage = thisgroup.submessage;
          $scope.leave = true;
        }
      });  
  }
  
	$scope.setGroup = function(group_name, u_groups) {
    $scope.group_name = group_name;
    $scope.u_groups = u_groups;
	}
  

  $scope.groupuserlist = function() {
    $scope.useradd = undefined;
    $scope.added = "";
    $scope.GroupUserListResource = $resource('http://:remote_url/listuser/group',
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Loading";
    var groupuserlistmeta = new $scope.GroupUserListResource($scope.groupmeta.data);
    groupuserlistmeta.$save(function(response) {
        var result = response;
        if (result.status === "success") {
          $scope.usersfound = result;
          if ($scope.usersfound.entities.length > 0) {
            $scope.useradd = $scope.usersfound.entities[0];
          } else {
            $scope.added = "No user(s) found!";
          }
        }
        $scope.waiting = "Ready";
     });  
  }  

  $scope.usertoadd = {};
  $scope.usertoadd.data = {"group_id":$scope.test, "users": []};
  $scope.useradd = undefined;
  
  $scope.includemember = function(useradd) {
    if (useradd == undefined) return;
    var check_add = false;
    for (var i = 0; i < $scope.usertoadd.data.users.length; i++) {
      var add = $scope.usertoadd.data.users[i];
      if (useradd.id === add.id) {
        $scope.added = "You cannot add the same user twice!";
        check_add = true;
        break;
      }
    }
    if (!check_add) {
      $scope.usertoadd.data.users.push(useradd);
      $scope.useradd = $scope.usersfound.entities[0];
      $scope.added = "";
    }
  }
  
  $scope.unincludemember = function(id) {
    var index = $scope.usertoadd.data.users.indexOf(id);
    $scope.usertoadd.data.users.splice(index, 1);
    $scope.added = "";
  }
  
  $scope.addmember = function() {
    $scope.added = "";
    $scope.usertoadd.data.group_id = $scope.test;
    $scope.AddMemberResource = $resource('http://:remote_url/adduser/group', 
                  {"remote_url":$scope.remote_url}, 
                  {'save': { method: 'POST',    params: {} }});
 
    $scope.waiting = "Saving";
    var addgroup = new $scope.AddMemberResource($scope.usertoadd.data);
    addgroup.$save(function(response) { 
            var result = response;
            $scope.usertoadd.data = {"users": [], "group_id":$scope.test};
            if (result.status === 'success') {
              $scope.waiting = "Error";
              $scope.heading = "Success!";
              $scope.message = "You have sent out the invite.";
              for (var i = 0; i < result.invited; i++) {
                $scope.submessage += result.invited[i] + "\n";
              }
            } else {
              $scope.waiting = "Error";
              $scope.heading = "Oops...!"
              $scope.message = result.message;
              $scope.submessage = result.submessage;
            }
          }); 
  }
  
  $scope.passfounder = function(id) {
    if ($scope.founder == true && $scope.belong == true) {
      bootbox.confirm("Do you really wish to make " + id.user + " the Founder?", function(foundAlert) {
        if (foundAlert === true) {
          $scope.passfounder = {};
          $scope.passfounder.data = id;
          $scope.PassFounderResource = $resource('http://:remote_url/passfounder/group', 
                        {"remote_url":$scope.remote_url}, 
                        {'save': { method: 'POST',    params: {} }});
          $scope.waiting = "Saving";
          var passfounder = new $scope.PassFounderResource($scope.passfounder.data);
          passfounder.$save(function(response) { 
                  var result = response;
                  $scope.usertoremove = {};
                  $scope.waiting = "Error";
                  $scope.heading = "Success!";
                  $scope.message = result.message;
                  $scope.submessage = result.submessage;
                }); 
          
        }
      });
    }
  }

  $scope.leavegroup = function() {
    if ($scope.founder == false && $scope.belong == true) {
      bootbox.confirm("Do you really wish to leave '" + $scope.group_name + "'?", function(leaveAlert) {
        if (leaveAlert === true) {
          var usertoremove = {'user_id': $scope.User.id,
                              'group_id': $scope.test,
                              'role': 'Member'}
          $scope.removemember(usertoremove);
        }
      });
    }
  }
  
  $scope.kickgroup = function(id) {
    if ($scope.founder == true && $scope.belong == true) {
      bootbox.confirm("Do you really wish to kick " + id.user + "?", function(kickAlert) {
        if (kickAlert === true) {
          $scope.removemember(id);
        }
      });
    }
  }
  
  $scope.removemember = function(id) {
    $scope.usertoremove = {};
    $scope.usertoremove.data = id;
    $scope.RemoveMemberResource = $resource('http://:remote_url/removeuser/group', 
                  {"remote_url":$scope.remote_url}, 
                  {'save': { method: 'POST',    params: {} }});
    $scope.waiting = "Saving";
    var removegroup = new $scope.RemoveMemberResource($scope.usertoremove.data);
    removegroup.$save(function(response) { 
            var result = response;
            $scope.usertoremove = {};
            if (result.status === 'success') {
              $scope.waiting = "Error";
              $scope.heading = "Success!";
              $scope.message = result.message;
              if (result.type === 'quit') {
                $scope.leave = true;
              }
            } else {
              $scope.waiting = "Error";
              $scope.heading = "Oops...!"
              $scope.message = result.message;
              $scope.submessage = result.submessage;
            }
          }); 
 
  }
  
  $scope.deletegroup = function() {
    if ($scope.founder == true && $scope.belong == true) {
      bootbox.confirm("Do you really wish to delete this group?", function(groupAlert) {
        if (groupAlert === true) {
          $scope.DeleteGroupResource = $resource('http://:remote_url/delete/group', 
                        {"remote_url":$scope.remote_url}, 
                        {'save': { method: 'POST',    params: {} }});
          $scope.waiting = "Saving";
          var deletegroup = new $scope.DeleteGroupResource($scope.groupmeta.data);
          deletegroup.$save(function(response) { 
              var result = response;
              if (result.status === 'success') {
                $scope.waiting = "Error";
                $scope.heading = "Success!";
                $scope.message = result.message;
                $scope.leave = true;
              } else {
                $scope.waiting = "Error";
                $scope.heading = "Oops...!"
                $scope.message = result.message;
                $scope.submessage = result.submessage;
              }
            }); 
        }
      });
    }
  }
      
  $scope.group_pagination = {"limit":5, "offset":0, "prev_offset":0, "next_offset":0};
  
  $scope.more_sketch = function() {
    $scope.group_pagination = {"limit":5, "offset":0, "prev_offset":0, "next_offset":0};
    $scope.list();
  }
  
  $scope.paginate_back = function() {
    
  }
  
  $scope.paginate_forward = function() {
    if ($scope.group_pagination.next_offset > 
        $scope.group_pagination.offset) {
      $scope.group_pagination.offset = $scope.group_pagination.next_offset;
      $scope.list();
    }
  }
  
  $scope.list = function(){
    $scope.groupmeta.data = {'id':$scope.test,
                            'criteria': "",
                            'limit': $scope.group_pagination.limit,
                            'offset': $scope.group_pagination.offset};
    $scope.ListResource = $resource('http://:remote_url/list/sketch/group',
             {"remote_url":$scope.remote_url}, 
             {'save': {method: 'POST', params:{} }});
    $scope.waiting = "Loading";
    var listmeta = new $scope.ListResource($scope.groupmeta.data);
    listmeta.$save(function(response) {
        $scope.items = response;
        $scope.group_pagination.next_offset = $scope.items.next_offset;
        $scope.waiting = "Ready";
     });  
  };
    
  
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
      $scope.get_group();
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
 
    $scope.waiting = "Saving";
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
            $scope.get_group();
          }); 
  };
  
  $scope.simpleSearch = function() {
    sharedFunctions.simpleSearch($scope.search);
  }
  $scope.getuser();
}