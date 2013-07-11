'use strict';
	
	//THIS FILE IS NOW USELESS, USELESS, USELESS!
	//MUDA MUDA MUDA MUDA MUDA MUDA MUDA MUDA MUDA MUDA........

	//Function to trigger a save procedure in the flash object
	//The flash object will call saveKSketchFile in return to pass the data from itself to javascript
	function initSave()
	{
		var swfObject = document.getElementById('KSketch2_Web');
		if(typeof swfObject !='undefined'){
			swfObject.save();//change load
			
		}
		else
		{
			alert('the swf object does not exist! Unable to save');
		}	
	}
	
	//Don't care about this, it just allows this example to load a file from
	//The text area
	function initLoad()
	{
		var textAreaObject = document.getElementById('visibleTextData');
		if(typeof textAreaObject !='undefined'){
			loadKSketchFile(textAreaObject.value);
			//loadKSketchFile(textAreaObject.innerText);
		}
		else
		{
			alert('no text area!');
		}	
	}

	// JavaScript Document
	
	//Function receives an xml string from the flash object
	//And displays it in the text box
	function saveKSketchFile(fileData)
	{
		//var textAreaObject = document.getElementById('visibleTextData');
		//textAreaObject.value = fileData;	
		
		e = document.getElementById('SaveSketch');
		scope = angular.element(e).scope();
		scope.$apply(function() {
			scope.setData(fileData);
		});	
	}
	
	//Function receives an xml string from anywhere
	//and asks the flash object to load it
	function loadKSketchFile(fileData)
	{
		var swfObject = document.getElementById('KSketch2_Web');
		if(typeof swfObject !='undefined'){
			swfObject.load(fileData);//change load
		}
		else
		{
			alert('the swf object does not exist! Unable to save');
		}	
	}