'use strict';

  var myApp = angular.module('myApp', ['ui.directives', 'ngResource']);
  myApp.service('sharedProperties', function() {
    //Set variable Reference for Janrain accounr name here!
    var accountJanrain = 'k-sketch';
    //Set variable Reference for Backend here!
    var backendUrl = 'k-sketch-test.appspot.com';
    
    return{
      getJanrainAccount: function() {
        return accountJanrain;
      },
      getBackendUrl: function() {
        return backendUrl;
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
  function debugStop() {
  	console.log("stop.");
  }
