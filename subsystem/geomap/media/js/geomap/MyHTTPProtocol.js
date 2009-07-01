MyHTTPProtocol = OpenLayers.Class(OpenLayers.Protocol.HTTP, {

    dynamicParams: null,

    read: function(options) {
	var dynamicParams = this.evaluateDynamicParams();
	var params = extend(this.params,
			    extend(options.params, dynamicParams));
	var extOptions = extend(options, {params: params});
	return OpenLayers.Protocol.HTTP.prototype.read.apply(this,
							     [extOptions]);
    },

    evaluateDynamicParams: function() {
	var params = {};
	for (var key in this.dynamicParams) {
	    var dp = this.dynamicParams[key];
	    params[key] = dp['function'].apply(dp['object']);
	}
	return params;
    },
    
    CLASS_NAME: "MyHTTPProtocol"
});    
