'use strict';

  var myApp = angular.module('myApp', ['ui.directives', 'ngResource']);
 //var myApp = angular.module('myApp', ['ngResource','ngMockE2E']);

  /*myApp.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/view1', {templateUrl: 'partials/partial1.html', controller: SketchController});
    $routeProvider.when('/view2', {templateUrl: 'partials/partial2.html', controller: SketchController});
    $routeProvider.otherwise({redirectTo: '/view1'});
  }]);*/