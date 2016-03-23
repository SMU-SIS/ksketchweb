'use strict';
var config = {
    "trackingID":"*** Enter your GAE tracking ID ***",
    "trackerName":"*** Enter your GAE host name ***"
}

  var myApp = angular.module('myApp', ['ui.directives', 'ngResource']);
  myApp.service('sharedProperties', function() {
    //Set variable Reference for Backend here!
    var backendUrl = 'localhost:8080';
    var ksketch_email = 'email@yourdomain.com';
    var facebookAppId = '*** Enter your Facebook appid from developer.facebook.com ****';
    return{
      getBackendUrl: function() {
        return backendUrl;
      },
       getKSketchEmail: function() {
        return ksketch_email;
      },
      getFacebookAppId: function() {
        return facebookAppId;
      }
    };

  });
  myApp.factory('sharedFunctions', function($window) {
    return{
      simpleSearch: function(search) {
        if (search.replace(/^\s+|\s+$/g,'') !== "") {
          var searchUrl = "search.html?query=" + search.replace(/^\s+|\s+$/g,'');
          window.location.href=searchUrl;
        }
        return searchUrl
      }
    }
  });

 //var myApp = angular.module('myApp', ['ngResource','ngMockE2E']);

  /*myApp.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/view1', {templateUrl: 'partials/partial1.html', controller: SketchController});
    $routeProvider.when('/view2', {templateUrl: 'partials/partial2.html', controller: SketchController});
    $routeProvider.otherwise({redirectTo: '/view1'});
  }]);*/