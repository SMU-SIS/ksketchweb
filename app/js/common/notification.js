function notifyAccept(n_id, groupData) {
  e = document.getElementById('testdiv');
  scope = angular.element(e).scope();
  scope.$apply(function() {
    scope.notify_accept(n_id, groupData);
  });	
}

function notifyReject(n_id, groupData) {
  e = document.getElementById('testdiv');
  scope = angular.element(e).scope();
  scope.$apply(function() {
    scope.notify_reject(n_id, groupData);
  });	
}