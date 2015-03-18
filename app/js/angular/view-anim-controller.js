/**
 * Created by ramvibhakar on 27-2-15.
 */
function ViewSVGController($scope, $resource, sharedProperties, sharedFunctions) {
    $scope.urltype = "-";
    $scope.urlid = 0;
    $scope.version = -1;
    $scope.waiting = "Ready";
    $scope.heading = "";
    $scope.message = "";
    $scope.test = -1;
    $scope.remote_url = sharedProperties.getBackendUrl();
    $scope.trans_json = "";
    $scope.paused = true;
    $scope.current_time = 0;
    $scope.last_update_time = 0;
    $scope.time_now = 0;
    $scope.cursor_index = 0;
    $scope.timer = 0;
    $scope.scene_complete = false;
    $scope.svg_data = "";
    $scope.max_time = 40;
    $scope.mySlider = null;
    $scope.setType = function (type, uid) {
        $scope.urltype = type;
        $scope.urlid = uid;
    };
    $scope.setTest = function (test) {
        $scope.test = test;
    };
    $scope.setVersion = function (version) {
        $scope.version = version;
    };
    $scope.get_sketch = function () {
        $scope.sketchmeta = {};
        $scope.sketchmeta.data = {'id': $scope.test, 'version': $scope.version};
        $scope.SketchResource = $resource('http://:remote_url/get/svg/view/' + $scope.test + '/' + $scope.version + '/0',
            {"remote_url": $scope.remote_url},
            {'save': {method: 'GET', params: {}}});
        $scope.waiting = "Loading";
        var sketchmeta = new $scope.SketchResource($scope.sketchmeta.data);
        sketchmeta.$save(function (response) {
            var check = response.status;
            if (check === "Forbidden") {
                $scope.waiting = "Error";
                $scope.heading = "Access Denied";
                $scope.message = "You have not been granted permission to view this sketch.";
                $scope.leave = true;
            } else if (check === "Error") {
                $scope.waiting = "Error";
                $scope.heading = "Oops...!";
                $scope.message = "We're sorry, but the sketch you wanted does not exist.";
                $scope.submessage = "Perhaps the URL that you entered was broken?";
                $scope.leave = true;
            } else {
                parser = new DOMParser();
                $scope.svg_data = response.data;
                doc = parser.parseFromString(response.data, "text/xml");
                document.getElementById("mainbody").appendChild(doc.firstChild);
                $scope.get_trans_json();
            }
        });
    };

    $scope.get_trans_json = function () {
        $scope.sketchmeta = {};
        $scope.sketchmeta.data = {'id': $scope.test, 'version': $scope.version};
        $scope.SketchResource = $resource('http://:remote_url/get/svg/script/' + $scope.test + '/' + $scope.version + '/0',
            {"remote_url": $scope.remote_url},
            {'save': {method: 'GET', params: {}}});
        var sketchmeta = new $scope.SketchResource($scope.sketchmeta.data);
        sketchmeta.$save(function (response) {
            var check = response.status;
            if (check === "Forbidden") {
                $scope.waiting = "Error";
                $scope.heading = "Access Denied";
                $scope.message = "You have not been granted permission to view this sketch.";
                $scope.leave = true;
            } else if (check === "Error") {
                $scope.waiting = "Error";
                $scope.heading = "Oops...!";
                $scope.message = "We're sorry, but the sketch you wanted does not exist.";
                $scope.submessage = "Perhaps the URL that you entered was broken?";
                $scope.leave = true;
            } else {
                $scope.trans_json = JSON.parse(response.timeline);
                $scope.max_time = $scope.trans_json[$scope.trans_json.length -1].t;
                $("#slider").attr("data-slider-max",$scope.max_time);
                $scope.mySlider = $("#slider").slider({
                    formatter: function (value) {
                        return 'Current value: ' + value;
                    }
                });
                $scope.mySlider.on("slideStop",$scope.sliderstop);
                $scope.waiting = "Ready";
            }
        });
        $scope.init_page();
        $scope.initScene();
    };
    $scope.sliderstop = function() {
        scope.$apply(function () {
            $scope.current_time = $scope.mySlider.slider('getValue');
        });
    };
    $scope.init_page = function() {
        document.addEventListener("keydown", $scope.KeyDown, true);
	    document.addEventListener("keyup", $scope.KeyUp, true);
	    document.addEventListener("keypress", $scope.KeyPress, false);
    };
    $scope.play_svg = function() {

        for (;$scope.cursor_index < $scope.trans_json.length && $scope.trans_json[$scope.cursor_index].t <= $scope.current_time; $scope.cursor_index++) {
            events = $scope.trans_json[$scope.cursor_index];
            time = events.t;
            for (j = 0; j < events.e.length; j++) {
                if (events.e[j].hasOwnProperty("trans"))
                    $scope.transform_svg( events.e[j].obj, events.e[j].trans);
                else
                    $scope.set_visibility( events.e[j].obj, events.e[j].v);
            }
        }
    };
    $scope.transform_svg = function (obj, trans) {
        if ( document.getElementById(obj).getAttribute("transform") != null) {
            document.getElementById(obj).setAttribute("transform", document.getElementById(obj).getAttribute("transform") + " matrix" + trans);
        } else {
            document.getElementById(obj).setAttribute("transform", "matrix" + trans);
        }
    };
    $scope.set_visibility = function (obj, val) {
        document.getElementById(obj).style.opacity = val;
    };
    $scope.initScene = function () {
        $scope.cursor_index = 0;
        $scope.current_time = 0;
        var d = new Date();
        $scope.last_update_time = d.getTime() + 31.25;
        $scope.timer = setInterval($scope.mainLoop, 31.25);
    };
    $scope.KeyPress = function (key) {
        if (key.keyCode == 32 )
            key.preventDefault();
    };
    $scope.KeyDown = function(key) {
        var code;
        if (window.event == undefined) {
            var code = key.keyCode;
        }
        else {
            code = window.event.keyCode;
        }
        if(code == 32) {
            $scope.pauseOrPlay();
        }
        key.preventDefault();
    };
    $scope.KeyUp = function KeyUp(key)
    {
	    var code;
        if (window.event == undefined) {
		    var code = key.keyCode;
	    }else {
		    code = window.event.keyCode;
	    }
        key.preventDefault();
    };
    $scope.pauseOrPlay = function () {
        if(!$scope.scene_complete) {
            $scope.paused = !$scope.paused;
            if ($scope.paused) {
                document.getElementById("button-icon").className = "icon-play";
            } else {
                document.getElementById("button-icon").className = "icon-pause";
            }
        } else {
            doc = parser.parseFromString($scope.svg_data, "text/xml");
            var mySVG = document.getElementById("mySVG");
            while(mySVG.firstChild) {
                mySVG.removeChild(mySVG.firstChild);
            }
            mySVG.appendChild(doc.firstChild.firstChild);
            $scope.$apply(function () {
                $scope.paused = false;
                $scope.scene_complete = false;
            });
            $scope.initScene();
            document.getElementById("button-icon").className = "icon-pause";
        }
    }
    $scope.mainLoop = function () {
        if($scope.waiting == "Ready" && $scope.cursor_index >= $scope.trans_json.length) {
            document.getElementById("button-icon").className = "icon-repeat";
            $scope.scene_complete = true;
            clearInterval($scope.timer);
        } else {
            if (!$scope.paused) {
                var d = new Date();
                $scope.time_now = d.getTime();
                $scope.$apply(function () {
                    $scope.current_time += ($scope.time_now  - $scope.last_update_time);
                });


            } else {
                var d = new Date();
                $scope.last_update_time = d.getTime();
            }
        }
    };
    $scope.$watch('current_time', function(newValue, oldValue) {
        if($scope.mySlider != null) {
             $scope.mySlider.slider('setValue', $scope.current_time);
        }
        if(newValue > oldValue) {
            $scope.play_svg();
            $scope.last_update_time = $scope.time_now;
        } else if( newValue < oldValue) {
            doc = parser.parseFromString($scope.svg_data, "text/xml");
            var mySVG = document.getElementById("mySVG");
            while(mySVG.firstChild) {
                mySVG.removeChild(mySVG.firstChild);
            }
            mySVG.appendChild(doc.firstChild.firstChild);
            for ($scope.cursor_index = 0;$scope.cursor_index < $scope.trans_json.length && $scope.trans_json[$scope.cursor_index].t <= $scope.current_time; $scope.cursor_index++) {
            events = $scope.trans_json[$scope.cursor_index];
            time = events.t;
            for (j = 0; j < events.e.length; j++) {
                if (events.e[j].hasOwnProperty("trans")) {
                    //document.getElementById(events.e[j].obj).setAttribute("transform",null);
                    $scope.transform_svg(events.e[j].obj, events.e[j].trans);
                }
                else {
                    $scope.set_visibility(events.e[j].obj, events.e[j].v);
                }
            }
        }
        }

    },true);

    $scope.year;
    $scope.setFooterYear = function () {
        var today = new Date(), today_year = today.getFullYear();
        $scope.year = today_year;
    };
    $scope.setFooterYear();
}
