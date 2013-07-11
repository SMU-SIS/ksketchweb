'use strict';

  //var myApp = angular.module('myApp', ['myApp.filters', 'myApp.services', 'myApp.directives','ngResource', 'analytics','ngMockE2E']);
  var myApp = angular.module('myApp', ['ngResource','ngMockE2E']);

  myApp.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/view1', {templateUrl: 'partials/partial1.html', controller: FirstController});
    $routeProvider.when('/view2', {templateUrl: 'partials/partial2.html', controller: FirstController});
    $routeProvider.otherwise({redirectTo: '/view1'});
  }]);

  myApp.run(function($httpBackend) {
      
      var annimations = [];
      var count = 1;
      var testAnnimation = {name: 'test', id:count};
      annimations.push(testAnnimation);
      
      //To simulate posts
      $httpBackend.whenPOST('/annimation').respond(function(method, url, data) {
        var newAnnimation = JSON.parse(data);
        count = count + 1;
        newAnnimation['id'] = count;
        annimations.push(newAnnimation);      
        return [200,newAnnimation];
    
      });
      
      //To simulate GETs
  	  //$httpBackend.whenGET('/player').respond(player);
      $httpBackend.whenGET(/^partials/).passThrough();
      //$httpBackend.whenGET(/^api/).passThrough();
      
	});