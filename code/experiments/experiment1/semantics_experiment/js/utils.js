
//this function parses a URL parameter of the form experiment.html?condition=
function get_url_param(name, defaultValue) { 
    var regexS = "[\?&]"+name+"=([^&#]*)"; 
    var regex = new RegExp(regexS); 
    var tmpURL = window.location.href; 
    var results = regex.exec(tmpURL); 
    if( results == null ) { 
        return defaultValue; 
    } else { 
        return results[1];    
    } 
}