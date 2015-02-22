/**
 * Created by ramvibhakar on 12-2-15.
 */
function ViewSVGController($scope, $resource,sharedProperties,sharedFunctions){
    //Search Query Filter
    $scope.query = function(item) {
        return !!((item.data.fileName.indexOf($scope.search || '') !== -1 || item.data.owner.indexOf($scope.search || '') !== -1));
    };

    //Sketch
    $scope.sketchModelId = "";  //Placeholder value for sketchId (identifies all sub-versions of the same sketch)
    $scope.fileData = "";  //Placeholder value for fileData (saved data)
    $scope.fileName = "";  //Placeholder value for fileName (name file is saved under)
    $scope.changeDescription = ""; //Placeholder value for changeDescription (change description for file edits)

    $scope.leave = false;
    $scope.test = -1;
    $scope.urltype = "-";
    $scope.urlid = 0;
    $scope.version = -1;
    $scope.heading = "";
    $scope.message = "";
    $scope.submessage = "";
    $scope.notify = "You have no new notification(s).";
    $scope.notify_icon = "icon-list-alt";
    $scope.trans_json = "";

    $scope.Model = $resource('http://:remote_url/:model_type/:id',
                        {},{'get': {method: 'JSONP', isArray: false, params:{callback: 'JSON_CALLBACK'}}
                           }
                    );
     $scope.remote_url = sharedProperties.getBackendUrl();
     $scope.janrain_ref = sharedProperties.getJanrainAccount();
     $scope.waiting = "Ready";
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

    $scope.get_sketch = function() {
      $scope.sketchmeta = {};
      $scope.sketchmeta.data = {'id':$scope.test, 'version':$scope.version};
      $scope.SketchResource = $resource('http://:remote_url/get/svg/view/'+$scope.test+'/'+$scope.version+'/0',
               {"remote_url":$scope.remote_url},
               {'save': {method: 'GET', params:{} }});
      $scope.waiting = "Loading";
      var sketchmeta = new $scope.SketchResource($scope.sketchmeta.data);
      sketchmeta.$save(function(response) {
          var check = response.status;
          if (check === "Forbidden") {
            $scope.waiting = "Error";
            $scope.heading = "Access Denied";
            $scope.message = "You have not been granted permission to view this sketch.";
            $scope.leave = true;
          } else if (check === "Error")  {
            $scope.waiting = "Error";
            $scope.heading = "Oops...!";
            $scope.message = "We're sorry, but the sketch you wanted does not exist.";
            $scope.submessage = "Perhaps the URL that you entered was broken?";
            $scope.leave = true;
          } else {
               console.log(response);
              $scope.waiting = "Ready";
              parser = new DOMParser();
              doc = parser.parseFromString(response.data, "text/xml");
              document.getElementById("mainbody").appendChild(doc.firstChild);
              $scope.get_trans_json();
          }
        });
    }

    $scope.get_trans_json = function() {
      $scope.sketchmeta = {};
      $scope.sketchmeta.data = {'id':$scope.test, 'version':$scope.version};
      $scope.SketchResource = $resource('http://:remote_url/get/svg/script/'+$scope.test+'/'+$scope.version+'/0',
               {"remote_url":$scope.remote_url},
               {'save': {method: 'GET', params:{} }});
      $scope.waiting = "Loading";
      var sketchmeta = new $scope.SketchResource($scope.sketchmeta.data);
      sketchmeta.$save(function(response) {
          var check = response.status;
          if (check === "Forbidden") {
            $scope.waiting = "Error";
            $scope.heading = "Access Denied";
            $scope.message = "You have not been granted permission to view this sketch.";
            $scope.leave = true;
          } else if (check === "Error")  {
            $scope.waiting = "Error";
            $scope.heading = "Oops...!";
            $scope.message = "We're sorry, but the sketch you wanted does not exist.";
            $scope.submessage = "Perhaps the URL that you entered was broken?";
            $scope.leave = true;
          } else {

              $scope.waiting = "Ready";
              $scope.trans_json = JSON.parse(response.timeline);
              for(i=0;i< $scope.trans_json.length;i++){
                  events = $scope.trans_json[i];
                  time = events.t;
                  for(j=0;j < events.e.length;j++) {
                      setTimeout( $scope.transform_svg, time,events.e[j].obj,events.e[j].trans);
                  }
              }
          }
        });
    }
    $scope.transform_svg= function (obj, trans) {
     //if(trans == "(0.999860268768,-0.0167165468423,0.0167165468423,0.999860268768,-5.78599721214,4.62546567632)")
      //  console.log("here");
        document.getElementById(obj).setAttribute("transform","matrix"+trans);
    }
    $scope.item = {};
        $scope.item.data = {"sketchId":"", "version":"", "originalSketch":"","originalVersion":"", "owner":"", "owner_id":"", "fileName":"", "fileData":"", "changeDescription":"", "appver":"", "p_view": true, "p_edit": true, "p_comment": true};


    $scope.setTest = function(test) {
      $scope.test = test;
    }

    $scope.setType = function(type,uid) {
      $scope.urltype = type;
      $scope.urlid = uid;
    }


    $scope.setVersion = function(version) {
      $scope.version = version;
    }


	$scope.setData = function(fileData) {
		$scope.fileData = fileData;
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
            });
    };

    $scope.comment = {};
        $scope.comment.data = {"sketchId":$scope.test, "version":$scope.version, "content":"", "replyToId":-1};

    $scope.addComment = function() {
      $scope.comment.data.sketchId = $scope.test;
      $scope.comment.data.version = $scope.version;
      if ($scope.comment.data.content.length > 0) {
        $scope.AddCommentResource = $resource('http://:remote_url/add/comment',
                      {"remote_url":$scope.remote_url},
                      {'save': { method: 'POST',    params: {} }});
        var add_comment = new $scope.AddCommentResource($scope.comment.data);
        add_comment.$save(function(response) {
                var result = response;
                $scope.comment.data = {"sketchId":$scope.test, "version":$scope.version, "content":"", "replyToId":-1};
                if (result.status !== 'success') {
                  $scope.waiting = "Error";
                  $scope.heading = "Oops...!"
                  $scope.message = result.message;
                  $scope.submessage = result.submessage;
                }
                $scope.getComments();
              });
      }
    }

    $scope.getComments = function() {
      $scope.commentmeta = {};
      $scope.commentmeta.data = {"id":$scope.test};
      $scope.GetCommentResource = $resource('http://:remote_url/get/comment',
                    {"remote_url":$scope.remote_url},
                    {'save': { method: 'POST',    params: {} }});
      var commentmeta = new $scope.GetCommentResource($scope.commentmeta.data);
      commentmeta.$save(function(response) {
          $scope.comments = response;
       });
    }

    $scope.like = {};
        $scope.like.data = {"sketchId":$scope.test, "version":$scope.version};

    $scope.toggleLike = function() {
      $scope.like.data.sketchId = $scope.test;
      $scope.like.data.version = $scope.version;
      $scope.ToggleLikeResource = $resource('http://:remote_url/toggle/like',
                    {"remote_url":$scope.remote_url},
                    {'save': { method: 'POST',    params: {} }});
      var toggle_like = new $scope.ToggleLikeResource($scope.like.data);
      toggle_like.$save(function(response) {
              var result = response;
              $scope.like.data = {"sketchId":$scope.test, "version":$scope.version};
              if (result.status !== 'success') {
                $scope.waiting = "Error";
                $scope.heading = "Oops...!"
                $scope.message = result.message;
                $scope.submessage = result.submessage;
              }
              $scope.getLikes();
            });
    }

    $scope.getLikes = function() {
      $scope.likemeta = {};
      $scope.likemeta.data = {"id":$scope.test};
      $scope.GetLikeResource = $resource('http://:remote_url/get/like',
              {"remote_url":$scope.remote_url},
              {'save': {method: 'POST', params:{} }});
      var likemeta = new $scope.GetLikeResource($scope.likemeta.data);
      likemeta.$save(function(response) {
          $scope.likes = response;
       });
    }
    $scope.simpleSearch = function() {
      sharedFunctions.simpleSearch($scope.search);
    }

    $scope.year;
    $scope.setFooterYear = function()
    {
      var today = new Date(),
          today_year = today.getFullYear();

      $scope.year = today_year;
    }

    $scope.setFooterYear();
    $scope.getuser();

}