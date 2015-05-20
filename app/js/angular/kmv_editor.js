/**
 * Created by ramvibhakar on 14/05/15.
 */
'use strict';

/* Controller for editkmv.html */

//angular.module('app', ['ngResource']);
function KMVEditor($scope, $resource, sharedProperties, sharedFunctions) {

    $scope.User = {
        "id": 0, "u_name": "Anonymous User", "u_realname": "Anonymous User",
        "u_login": false, "u_email": "", "g_hash": "", "u_created": "",
        "u_lastlogin": "", "u_logincount": "", "u_version": 1.0,
        "u_isadmin": false, "u_isactive": false, "is_approved": false,
        "birth_month": "", "birth_year": "", "parent_email": "",
        "contact_studies": true, "contact_updates": true
    };
    $scope.sketch_id;
    $scope.profile_user = {
        "id": 0, "u_name": "Anonymous User", "u_realname": "Anonymous User",
        "u_login": false, "u_email": "", "g_hash": "", "u_created": "",
        "u_lastlogin": "", "u_logincount": "", "u_version": 1.0,
        "u_isadmin": false, "u_isactive": false, "is_approved": false,
        "birth_month": "", "birth_year": "", "parent_email": "",
        "contact_studies": true, "contact_updates": true
    };
    $scope.currentPage = 1,
        $scope.totalSketches = 0
        , $scope.numPerPage = 5
        , $scope.maxSize = 5
        , $scope.dataLoaded = false
        , $scope.reverse = true
        , $scope.icon = 'down'
        , $scope.sorted_by = 'created'
        , $scope.sort_description = 'Date Created'
        , $scope.direction_description = 'Descending';


    $scope.backend_locations = [
        {url: sharedProperties.getBackendUrl(), urlName: 'remote backend'},
        {url: 'localhost:8080', urlName: 'localhost'}];

    $scope.showdetails = false;

    //Date (Time Zone) Format
    $scope.tzformat = function (utc_date) {

        var d = moment(utc_date, "DD MMM YYYY HH:mm:ss");
        return d.format("dddd, Do MMM YYYY, hh:mm:ss");
    };

    $scope.search = "";
    $scope.selected_search = "Name";

    $scope.newgroup = {};
    $scope.newgroup.data = {"group_name": "", "user_id": ""};

    $scope.test = "-";
    $scope.urltype = "-";
    $scope.profilemeta = {};
    $scope.profilemeta.data = {'id': 0};

    $scope.editprofilemeta = {};
    $scope.editprofilemeta.data = {
        'id': 0,
        'u_displayname': "",
        'contact_updates': false,
        'contact_studies': false,
        'edit_type': 'self'
    };


    $scope.reload = false;
    $scope.heading = "";
    $scope.message = "";
    $scope.submessage = "";
    $scope.notify = "You have no new notification(s).";
    $scope.notify_icon = "icon-list-alt";
    $scope.editor;

    //Search Query Filter
    $scope.query = function (item) {
        return !!((item.data.fileName.indexOf($scope.search || '') !== -1 || item.data.owner.indexOf($scope.search || '') !== -1));
    };

    $scope.predicate_users = '-data.fileName';


    //Replace this url with your final URL from the SingPath API path.
    //$scope.remote_url = "localhost:8080";
    $scope.remote_url = sharedProperties.getBackendUrl();
    $scope.waiting = "Ready";

    //resource calls are defined here

    $scope.Model = $resource('http://:remote_url/:model_type/:id',
        {}, {'get': {method: 'JSONP', isArray: false, params: {callback: 'JSON_CALLBACK'}}}
    );

    $scope.getuser = function () {
        $scope.UserResource = $resource('http://:remote_url/user/getuser',
            {'remote_url': $scope.remote_url},
            {
                'get': {method: 'JSONP', isArray: false, params: {callback: 'JSON_CALLBACK'}}
            });
        $scope.waiting = "Loading";
        $scope.UserResource.get(function (response) {
            var result = response;
            if (result.u_login === "True" || result.u_login === true) {
                $scope.User = result;
                $scope.User.u_created = $scope.tzformat($scope.User.u_created);

                if ($scope.User.u_lastlogin !== "") {
                    $scope.User.u_lastlogin = $scope.tzformat($scope.User.u_lastlogin);
                }
            } else {
                $scope.User = {
                    "id": 0, "u_name": "Anonymous User", "u_realname": "Anonymous User",
                    "u_login": false, "u_email": "", "g_hash": "", "u_created": "",
                    "u_lastlogin": "", "u_logincount": "", "u_version": 1.0,
                    "u_isadmin": false, "u_isactive": false, "is_approved": false,
                    "birth_month": "", "birth_year": "", "parent_email": "",
                    "contact_studies": true, "contact_updates": true
                };
            }

            $scope.determineAccess();
            $scope.waiting = "Ready";
        });
    }

    $scope.determineAccess = function () {

        if ($scope.User.id > 0) {
            if ($scope.User.is_approved) {
                if(!$scope.User.u_isadmin) {
                    window.location.replace("profile.html");
                }
            } else {
                    window.location.replace("register.html");
            }
        }
    }

    $scope.setTest = function (test) {
        $scope.test = test;
    }

    $scope.setType = function (type) {
        $scope.urltype = type;
    }


    $scope.simpleSearch = function () {
        sharedFunctions.simpleSearch($scope.search);
    }


    $scope.year;
    $scope.setFooterYear = function () {
        var today = new Date(),
            today_year = today.getFullYear();

        $scope.year = today_year;
    }

    $scope.getXML = function () {
        $scope.XMLResource = $resource('http://:remote_url/get/sketch/view_xml/' + $scope.sketch_id + '/-1/' + $scope.User.id,
            {'remote_url': $scope.remote_url},
            {
                'get': {method: 'GET', isArray: false}
            });
        $scope.waiting = "Loading";
        $scope.XMLResource.get(function (response) {
            if (response.status == "Error") {
                $scope.waiting = "Error";
                $scope.heading = "Hmm...";
                $scope.message = "Either you donot have admin priviledge";
                $scope.submessage = "Or the sketch is not found";
            } else if (response.data.fileData) {
                $scope.editor.set('value', $scope.formatXml(response.data.fileData));
                $scope.editor.set('mode', 'xml');
            }
            $scope.waiting = "Ready";
        });
    }

    $scope.saveXML = function () {

        var post_data = {
            "id": $scope.sketch_id,
            "fileData": $scope.editor.get('value'),
            "user_id": $scope.User.id
        };
        $scope.SaveResource = $resource('http://:remote_url/modify/fileData',
            {"remote_url": $scope.remote_url},
            {'save': {method: 'POST', params: {}}});
        $scope.waiting = "Loading";
        var savemeta = new $scope.SaveResource(post_data);
        savemeta.$save(function (response) {
            if (response.success == "false") {
                $scope.waiting = "Error";
                $scope.heading = "Hmm...";
                $scope.message = "Save was not successfull";
                $scope.submessage = "Please check if you have permissions or if the sketch exist";
            } else {
                $scope.waiting = "Error";
                $scope.heading = "Saved";
                $scope.message = "The sketch is saved successfully";
                $scope.submessage = "";
            }
        });
        $scope.waiting = "Ready";
    }

    $scope.formatXml = function (xml) {
        var reg = /(>)\s*(<)(\/*)/g; // updated Mar 30, 2015
        var wsexp = / *(.*) +\n/g;
        var contexp = /(<.+>)(.+\n)/g;
        xml = xml.replace(reg, '$1\n$2$3').replace(wsexp, '$1\n').replace(contexp, '$1\n$2');
        var pad = 0;
        var formatted = '';
        var lines = xml.split('\n');
        var indent = 0;
        var lastType = 'other';
        // 4 types of tags - single, closing, opening, other (text, doctype, comment) - 4*4 = 16 transitions
        var transitions = {
            'single->single': 0,
            'single->closing': -1,
            'single->opening': 0,
            'single->other': 0,
            'closing->single': 0,
            'closing->closing': -1,
            'closing->opening': 0,
            'closing->other': 0,
            'opening->single': 1,
            'opening->closing': 0,
            'opening->opening': 1,
            'opening->other': 1,
            'other->single': 0,
            'other->closing': -1,
            'other->opening': 0,
            'other->other': 0
        };

        for (var i = 0; i < lines.length; i++) {
            var ln = lines[i];
            var single = Boolean(ln.match(/<.+\/>/)); // is this line a single tag? ex. <br />
            var closing = Boolean(ln.match(/<\/.+>/)); // is this a closing tag? ex. </a>
            var opening = Boolean(ln.match(/<[^!].*>/)); // is this even a tag (that's not <!something>)
            var type = single ? 'single' : closing ? 'closing' : opening ? 'opening' : 'other';
            var fromTo = lastType + '->' + type;
            lastType = type;
            var padding = '';

            indent += transitions[fromTo];
            for (var j = 0; j < indent; j++) {
                padding += '\t';
            }
            if (fromTo == 'opening->closing')
                formatted = formatted.substr(0, formatted.length - 1) + ln + '\n'; // substr removes line break (\n) from prev loop
            else
                formatted += padding + ln + '\n';
        }

        return formatted;
    }
    $scope.acknowledge = function () {
        if ($scope.leave === true) {
            if (navigator.userAgent.match(/MSIE\s(?!9.0)/)) {
                var referLink = document.createElement("a");
                referLink.href = "index.html";
                document.body.appendChild(referLink);
                referLink.click();
            }
            else {
                window.location.replace("index.html");
            }
        } else {
            $scope.waiting = "Ready";
            $scope.heading = "";
            $scope.message = "";
            $scope.submessage = "";
        }
    }
    $scope.setFooterYear();
    $scope.getuser();
}