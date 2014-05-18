'use strict';

/* Controller for index.html */

//angular.module('app', ['ngResource']);
function LoginController($scope,$resource,sharedProperties, sharedFunctions){
    
  $scope.year;
  $scope.setFooterYear = function()
  {
    var today = new Date(),
        today_year = today.getFullYear();

    $scope.year = today_year;
  }

  $scope.setFooterYear();
}