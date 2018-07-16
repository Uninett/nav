define([], function() {

    /**
     * http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
     *
     * Returns querystring as a key => list[value] construct
     */
    function deSerialize(query) {
        query = typeof query === 'undefined' ?
            window.location.search.substring(1) :
            query.split('?').pop().split('#').shift();
        var urlParams;
        var match,
            pl     = /\+/g,  // Regex for replacing addition symbol with a space
            search = /([^&=]+)=?([^&]*)/g,
            decode = function (s) { return decodeURIComponent(s.replace(pl, " ")); };
        urlParams = {};
        while ((match = search.exec(query))) {
            var key = decode(match[1]);
            if (key in urlParams) {
                urlParams[key].push(decode(match[2]));
            } else {
                urlParams[key] = [decode(match[2])];
            }
        }
        return urlParams;
    }


    /**
     * http://stackoverflow.com/questions/1714786/querystring-encoding-of-a-javascript-object
     * 
     * Serialize object to querystring
     */
    function serialize(obj) {
        var str = [];
        for(var p in obj)
            if (obj.hasOwnProperty(p)) {
                str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
            }
        return str.join("&");
    }


    /**
     * Removes an url parameter from the querystring
     */
    function removeURLParameter(url, parameter) {
        //prefer to use l.search if you have a location/link object
        var urlparts= url.split('?');   
        if (urlparts.length>=2) {

            var prefix= encodeURIComponent(parameter)+'=';
            var pars= urlparts[1].split(/[&;]/g);

            //reverse iteration as may be destructive
            for (var i= pars.length; i-- > 0;) {    
                //idiom for string.startsWith
                if (pars[i].lastIndexOf(prefix, 0) !== -1) {  
                    pars.splice(i, 1);
                }
            }

            url= urlparts[0]+'?'+pars.join('&');
            return url;
        } else {
            return url;
        }
    }


    return {
        'deSerialize': deSerialize,
        'serialize': serialize,
        'removeURLParameter': removeURLParameter
    };
    
});

