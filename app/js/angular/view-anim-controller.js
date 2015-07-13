/*
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
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
    $scope.time_step = "";
    $scope.timeline = {};
    $scope.centers = "";
    $scope.paused = true;
    $scope.current_time = 0;
    //$scope.last_update_time = 0;
    $scope.time_now = 0;
    //$scope.cursor_index = 0;
    $scope.timer = 0;
    $scope.scene_complete = false;
    $scope.svg_data = "";
    $scope.max_time = 0;
    $scope.mySlider = null;
    $scope.default_frame = "";
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
                bootbox.alert(response.message);
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
                $("#mySVG").replaceWith(doc.firstChild);
                $scope.get_timeline();
            }
        });
    };


    // Looks up the object property in the timeline and returns it.
    // If the property does not exist at that time, takes the property from
    // The default_frame.
    $scope.get_frame_property = function (time, obj, prop) {
        var val;
        var t = Math.floor(time);
        if ($scope.timeline[t] && $scope.timeline[t][obj]) {
            val = $scope.timeline[t][obj][prop];
        }
        if (val === undefined) {
            return $scope.timeline[0][obj][prop];
        }
        return val;
    };

    $scope.get_timeline = function () {
        $scope.sketchmeta = {};
        $scope.sketchmeta.data = {'id': $scope.test, 'version': $scope.version};
        $scope.SketchResource = $resource('http://:remote_url/get/svg/script/' + $scope.test + '/' + $scope.version + '/0',
            {"remote_url": $scope.remote_url},
            {'save': {method: 'GET', params: {}}});
        var sketchmeta = new $scope.SketchResource($scope.sketchmeta.data);
        sketchmeta.$save(function (response) {
            var check = response.status;
            var t, i, o, k, eq, frames, frame, center, prev_time, prev_frame, tmp_frame, new_frame, prev_prop, cur_prop;
            var visible;

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
                //$scope.trans_json = response.timeline;
                //$scope.max_time = $scope.trans_json[$scope.trans_json.length -1].t;
                //$("#slider").attr("data-slider-max",$scope.max_time);
                //$scope.mySlider = $("#slider").slider({
                //    formatter: function (value) {
                //        return 'Current value: ' + value;
                //    }
                //});

                $scope.centers = response.centers;
                $scope.time_step = response.time_step;
                $scope.max_time = response.max_time;
                $scope.default_frame = response.default_frame;
                $scope.timeline = { 0: {} };

                for (o in $scope.centers) {
                    $scope.timeline[0][o] = $scope.default_frame;
                }
                prev_time = 0;
                tmp_frame = {};

                // We iterate while t < max_time + 1, not while t <= max_time,
                // because max_time may have had its decimal points truncated.
                for (t = 0; t < $scope.max_time+1; t += $scope.time_step) {
                    frames = response.timeline[Math.floor(t)];

                    // Process all those objects with frame records at this time
                    if (frames) {
                        for (i = 0; i < frames.length; i++) {
                            o = frames[i].id;

                            // Get the current frame.
                            for (k in $scope.default_frame) {
                                prev_prop = $scope.get_frame_property(prev_time, o, k);
                                cur_prop = frames[i][k];
                                if (cur_prop === undefined) {
                                    cur_prop = prev_prop;
                                }
                                tmp_frame[k] = cur_prop;
                            }

                            // If the frame differs from the frame at time 0, set a flag and prepare to create a new frame.
                            // If this is time 0, then include all properties (since this will replace the current default).
                            // Otherwise, include only those properties that differ from the frame at time 0, and only
                            // include properties other than 'v' if 'v' !== 0 (because the others don't matter in this case).
                            eq = true;
                            visible = tmp_frame.v !== 0;
                            for (k in $scope.default_frame) {
                                if (t === 0 ||
                                    ((k === 'v' || visible) && tmp_frame[k] !== $scope.timeline[0][o][k])) {
                                    eq = false;
                                } else {
                                    tmp_frame[k] = undefined;
                                }
                            }

                            if (!eq) {
                                new_frame = {};
                                for (k in $scope.default_frame) {
                                    if (tmp_frame[k] !== undefined) {
                                        new_frame[k] = tmp_frame[k];
                                    }
                                }
                                if (!$scope.timeline[Math.floor(t)]) {
                                    $scope.timeline[Math.floor(t)] = {};
                                }
                                $scope.timeline[Math.floor(t)][o] = new_frame;
                            }
                        }
                    }

                    // For all remaining objects, just use previous frame (if it exists).
                    // If the previous frame is at time 0, then there is no need to insert, because this is the default.
                    for (o in $scope.centers) {
                        frame = undefined;
                        if ($scope.timeline[Math.floor(t)]) {
                            frame = $scope.timeline[Math.floor(t)][o];
                        }
                        if (!frame && prev_time != 0 && $scope.timeline[Math.floor(prev_time)]) {
                            prev_frame = $scope.timeline[Math.floor(prev_time)][o];
                            if (prev_frame) {
                                if (!$scope.timeline[Math.floor(t)]) {
                                    $scope.timeline[Math.floor(t)] = {};
                                }
                                $scope.timeline[Math.floor(t)][o] = prev_frame;
                            }

                        }
                    }

                    prev_time = t;
                }

                $("#slider").attr("data-slider-max",$scope.max_time);
                $("#slider").attr("data-slider-step",$scope.time_step);
                $scope.mySlider = $("#slider").slider({
                    formatter: function (value) {
                        return (value/1000).toFixed(1)+" s";
                    }
                });

                //$scope.mySlider.on("slideStop",$scope.sliderstop);
                $scope.mySlider.on("slide",$scope.onslide);
                $scope.waiting = "Ready";
                $scope.init_page();
                $scope.initScene();
            }
        });

    };
    $scope.sliderstop = function() {
        scope.$apply(function () {
            $scope.current_time = $scope.mySlider.slider('getValue');
        });
    };

    $scope.onslide = function() {
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
        var o, x, y, r, s, v;
        for (o in $scope.centers) {
            x = $scope.get_frame_property($scope.current_time, o, 'x');
            y = $scope.get_frame_property($scope.current_time, o, 'y');
            r = $scope.get_frame_property($scope.current_time, o, 'r');
            s = $scope.get_frame_property($scope.current_time, o, 's');
            v = $scope.get_frame_property($scope.current_time, o, 'v');

            $scope.transform_svg(o, $scope.centers[o], x, y, r, s);
            $scope.set_visibility(o, v);
        }

        //for (;$scope.cursor_index < $scope.trans_json.length && $scope.trans_json[$scope.cursor_index].t <= $scope.current_time; $scope.cursor_index++) {
        //    events = $scope.trans_json[$scope.cursor_index];
        //    time = events.t;
        //    for (j = 0; j < events.e.length; j++) {
        //        if (events.e[j].hasOwnProperty("trans"))
        //            $scope.transform_svg( events.e[j].obj, events.e[j].trans);
        //        else
        //            $scope.set_visibility( events.e[j].obj, events.e[j].v);
        //    }
        //}
    };
    $scope.transform_svg = function (obj, c, x, y, r, s) {
        var trans1 = "";
        var rot = "";
        var scale = "";
        var trans2 = "";

        if (c.x !== 0 || c.y !== 0) {
            trans1 = "translate(" + (-c.x) + "," + (-c.y) + ") ";
        }
        if (r !== 0) {
            rot = "rotate(" + ((r * 180)/Math.PI) + ") ";
        }
        if (s !== 1) {
            scale = "scale(" + s + ") ";
        }
        if (c.x !== 0 || c.y !== 0 || x !== 0 || y !== 0) {
            trans2 = "translate(" + (c.x + x) + "," + (c.y+ y) + ") ";
        }

        document.getElementById(obj).setAttribute("transform", trans2 + rot + scale + trans1);

    };
    //$scope.transform_svg = function (obj, trans) {
    //    if ( document.getElementById(obj).getAttribute("transform") != null) {
    //        document.getElementById(obj).setAttribute("transform", document.getElementById(obj).getAttribute("transform") + " matrix" + trans);
    //    } else {
    //        document.getElementById(obj).setAttribute("transform", "matrix" + trans);
    //    }
    //};
    $scope.set_visibility = function (obj, val) {
        document.getElementById(obj).style.opacity = val;
    };
    $scope.initScene = function () {
        //$scope.cursor_index = 0;
        $scope.current_time = 0;
        //var d = new Date();
        //$scope.last_update_time = d.getTime() + $scope.time_step;
        $scope.timer = setInterval($scope.mainLoop, $scope.time_step);
        $scope.play_svg();
    };
    $scope.KeyPress = function (key) {
        if (key.keyCode == 32 )
            key.preventDefault();
    };
    $scope.KeyDown = function(key) {
        var code;
        if (window.event == undefined) {
            code = key.keyCode;
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
		    code = key.keyCode;
	    }else {
		    code = window.event.keyCode;
	    }
        key.preventDefault();
    };
    $scope.pauseOrPlay = function (event) {
        if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
            event.preventDefault();
        }
        if(!$scope.scene_complete) {
            $scope.paused = !$scope.paused;
            if ($scope.paused) {
                document.getElementById("button-icon").className = "glyphicon glyphicon-play";
            } else {
                document.getElementById("button-icon").className = "glyphicon glyphicon-pause";
            }
        } else {
            //doc = parser.parseFromString($scope.svg_data, "text/xml");
            //var mySVG = document.getElementById("mySVG");
            //while(mySVG.firstChild) {
            //    mySVG.removeChild(mySVG.firstChild);
            //}
            //mySVG.appendChild(doc.firstChild.firstChild);
            $scope.paused = false;
            $scope.scene_complete = false;
            $scope.initScene();
            document.getElementById("button-icon").className = "glyphicon glyphicon-pause";
        }
    };
    $scope.mainLoop = function () {
        if($scope.waiting == "Ready" && $scope.current_time >= $scope.max_time) {
            document.getElementById("button-icon").className = "glyphicon glyphicon-repeat";
            $scope.scene_complete = true;
            clearInterval($scope.timer);
        } else {
            if (!$scope.paused) {
                //var d = new Date();
                //$scope.time_now = d.getTime();
                $scope.$apply(function () {
                    //$scope.current_time += ($scope.time_now  - $scope.last_update_time);
                    $scope.current_time += $scope.time_step;
                });
            } //else {
            //    var d = new Date();
            //    $scope.last_update_time = d.getTime();
            //}
        }
    };
    $scope.$watch('current_time', function(newValue, oldValue) {
        if($scope.mySlider != null) {
             $scope.mySlider.slider('setValue', $scope.current_time);
        }
        if(newValue != oldValue) {
            $scope.play_svg();
        }
        //if(newValue > oldValue) {
        //    $scope.play_svg();
        //    $scope.last_update_time = $scope.time_now;
        //} else if( newValue < oldValue) {
        //    doc = parser.parseFromString($scope.svg_data, "text/xml");
        //    var mySVG = document.getElementById("mySVG");
        //    while(mySVG.firstChild) {
        //        mySVG.removeChild(mySVG.firstChild);
        //    }
        //    mySVG.appendChild(doc.firstChild.firstChild);
        //    for ($scope.cursor_index = 0;$scope.cursor_index < $scope.trans_json.length && $scope.trans_json[$scope.cursor_index].t <= $scope.current_time; $scope.cursor_index++) {
        //        events = $scope.trans_json[$scope.cursor_index];
        //        time = events.t;
        //        for (j = 0; j < events.e.length; j++) {
        //            if (events.e[j].hasOwnProperty("trans")) {
        //                $scope.transform_svg(events.e[j].obj, events.e[j].trans);
        //            }
        //            else {
        //                $scope.set_visibility(events.e[j].obj, events.e[j].v);
        //            }
        //        }
        //    }
        //}

    },true);

    $scope.year;
    $scope.facebookAppId = sharedProperties.getFacebookAppId();
    $scope.setFooterYear = function () {
        var today = new Date(), today_year = today.getFullYear();
        $scope.year = today_year;
    };
    $scope.setFooterYear();
}
