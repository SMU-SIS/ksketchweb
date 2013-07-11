'use strict';

/* Controllers */

//angular.module("myApp", []);
function FirstController($scope,$resource) {
    $scope.name = "Prof. Richard";
    
    //resource
    $scope.backend_locations = "";
    
	//local
  	$scope.fileData = "?";  
   	$scope.fileName = "";

	$scope.filearray = [];

	$scope.save = function() {

		$scope.fileData = $scope.fileData.replace(/(\r\n|\n|\r)/gm," ");
		$scope.filearray.push({id: $scope.filearray.length + 1, name: $scope.fileName, data: $scope.fileData})
	   	$scope.fileData = "";

	}
   
	$scope.setData = function(f) {
		$scope.fileData = f;
	}
}