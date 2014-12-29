'use strict';

/* Controller for search.html */

//angular.module('app', ['ngResource']);
function SearchController($scope,$filter,$resource,sharedProperties, sharedFunctions){
    $scope.filteredEntities = []
  ,$scope.currentPage = 0
  ,$scope.numPerPage = 5
  ,$scope.maxSize = 5
    ,$scope.dataLoaded=false
    ,$scope.reverse=true
    ,$scope.icon='down'
    ,$scope.sorted_by='created_d'
    ,$scope.sort_description='Date Created'
    ,$scope.direction_description="Descending";
	$scope.User = {
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

  $scope.search = "";
  $scope.search_notice = "";
  $scope.predicate_users = '-created';
  $scope.remote_url = sharedProperties.getBackendUrl();
  $scope.janrain_ref = sharedProperties.getJanrainAccount();
  $scope.waiting = "Ready";
  $scope.test = "-";
  $scope.notify = "You have no new notification(s).";
  $scope.notify_icon = "icon-list-alt";

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
            $scope.User = {
                          "id": 0, "u_name" :"Anonymous User",  "u_realname" :"Anonymous User",
                          "u_login": false, "u_email": "", "g_hash": "", "u_created": "",
                          "u_lastlogin": "", "u_logincount": "", "u_version": 1.0,
                          "u_isadmin": false, "u_isactive": false, "is_approved": false,
                          "birth_month": "", "birth_year": "", "parent_email": "",
                          "contact_studies": true, "contact_updates": true
                          };
            $scope.waiting = "Ready";
          }

          $scope.waiting = "Ready";
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
    $scope.search = test;
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

    $scope.waiting = "Updating";
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
          });
  };

  $scope.acknowledge = function() {
    $scope.waiting = "Ready";
    $scope.heading = "";
    $scope.message = "";
    $scope.submessage = "";
  }

  $scope.search_pagination = {"limit":5, "offset":0, "prev_offset":0, "next_offset":0};

  $scope.new_search = function() {
    $scope.search_pagination = {"limit":5, "offset":0, "prev_offset":0, "next_offset":0};
    $scope.searchlist();
  }

  $scope.paginate_back = function() {

  }

  $scope.paginate_forward = function() {
   $scope.currentPage =$scope.currentPage + 1;
  }

    $scope.numPages = function() {
       try {
           return Math.ceil($scope.searchitems.entities.length / $scope.numPerPage);
       }catch(err) {
           return 0;
       }
    }
    $scope.$watch('currentPage + numPerPage', function() {
        if($scope.dataLoaded) {
            var begin = (($scope.currentPage - 1) * $scope.numPerPage)
                , end = begin + $scope.numPerPage;

            $scope.filteredEntities = $scope.searchitems.entities.slice(begin, end);
        }
  },true);
    $scope.$watch('searchitems.entities', function() {
        if($scope.dataLoaded) {
            var begin = (($scope.currentPage - 1) * $scope.numPerPage)
                , end = begin + $scope.numPerPage;

            $scope.filteredEntities = $scope.searchitems.entities.slice(begin, end);
        }
  },true);
  $scope.searchlist = function(){
    if ($scope.search !== "") {
      $scope.searchmeta = {};
      $scope.searchmeta.data = {"criteria":$scope.search,
                                "show":'latest',
                                "limit":$scope.search_pagination.limit,
                                "offset":$scope.search_pagination.offset};
      $scope.SearchResource = $resource('http://:remote_url/list/sketch',
               {"remote_url":$scope.remote_url},
               {'save': {method: 'POST', params:{} }});
      $scope.waiting = "Loading";
      var searchmeta = new $scope.SearchResource($scope.searchmeta.data);
      searchmeta.$save(function(response) {
          $scope.searchitems = response;
          for(var i=0;i<$scope.searchitems.entities.length;i++) {
              $scope.searchitems.entities[i].created_d = new Date($scope.searchitems.entities[i].created);
              $scope.searchitems.entities[i].modified_d= new Date($scope.searchitems.entities[i].modified);
          }
          $scope.search_pagination.next_offset = $scope.searchitems.next_offset;
          $scope.search_notice = $scope.search;
          $scope.waiting = "Ready";
          $scope.dataLoaded=true;
          $scope.currentPage=1;
      });
    }
  };

  $scope.year;
  $scope.setFooterYear = function()
  {
    var today = new Date(),
        today_year = today.getFullYear();

    $scope.year = today_year;
  }
     var orderBy = $filter('orderBy');

    $scope.order = function(predicate) {
    if($scope.reverse)
        $scope.icon='down';
    else
        $scope.icon='up';
    $scope.sorted_by=predicate;
    $scope.searchitems.entities = orderBy($scope.searchitems.entities, predicate, $scope.reverse);
  };

     $scope.reorder = function() {
    $scope.searchitems.entities = orderBy($scope.searchitems.entities, $scope.sorted_by, $scope.reverse);
  };

  $scope.setFooterYear();
  $scope.getuser();
}