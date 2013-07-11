/* This is changed based on the site registered in Google APIs! */

var clientId = '956651233630.apps.googleusercontent.com';
var apiKey = 'AIzaSyCIR4gJHND-tweKRydRuNLHFWQ8Visnpaw';
var scopes = 'https://www.googleapis.com/auth/plus.me';

/* This is changed based on the site registered in Google APIs! */

	function handleClientLoad() {
	  gapi.client.setApiKey(apiKey);
	  window.setTimeout(checkAuth,1);
	}

	function checkAuth() {
	  gapi.auth.authorize({client_id: clientId, scope: scopes, immediate: true}, handleAuthResult);
	}

	function handleAuthResult(authResult) {
	  var authorizeButton = document.getElementById('authorize-button');
	  if (authResult && !authResult.error) {
	    authorizeButton.style.visibility = 'hidden';
	    makeApiCall();
	  } else {
	    authorizeButton.style.visibility = '';
	    authorizeButton.onclick = handleAuthClick;
	  }
	}

	function handleAuthClick(event) {
	  gapi.auth.authorize({client_id: clientId, scope: scopes, immediate: false}, handleAuthResult);
	  return false;
	}
	
	function makeApiCall() {
		  gapi.client.load('plus', 'v1', function() {
		      var request = gapi.client.plus.people.get({
		          'userId': 'me'
		            });
		      request.execute(function(resp) { //what else is inside this???? Hmm........
		          //var heading = document.createElement('h4');
		          //var image = document.createElement('img');
		          //image.src = resp.image.url;
		          //heading.appendChild(image);
		          //heading.appendChild(document.createTextNode(resp.displayName));
		    	  //document.getElementById('heading').innerText = resp.displayName;
		    	  
		    	  l = document.getElementById('heading');
		    	  loginscope = angular.element(l).scope();
		    	  loginscope.$apply(function(){
		    		 loginscope.setName(resp) ;
		    	  });
		    	  
		          //document.getElementById('content').appendChild(heading);
		        });
		    });
		}