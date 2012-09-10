//var require_base = "media/js/netmap"
var require_base = "media/js/netmap"
var require = {
	paths: {
		netmap: require_base,
		loader: require_base+'/libs/backbone/loader',
		jQuery: require_base+'/libs/jquery/jquery',
		jQueryUI: require_base+'../jquery-ui-1.8.21.custom.min',
		Underscore: require_base+'/libs/underscore/underscore',
		Handlebars: require_base+'/libs/handlebars/handlebars',
		Backbone: require_base+'/libs/backbone/backbone',
		order: require_base+"/order",
		text: require_base+"/text",
		templates: require_base+'/templates',
		NetmapExtras: 'media/js/netmap-extras',
		
		"libs/jquery/jquery-full": require_base+"/libs/jquery/jquery-full",
		"libs/underscore/underscore-full": require_base+"/libs/underscore/underscore-full",
		"libs/handlebars/handlebars-full": require_base+"/libs/handlebars/handlebars-full",
		"libs/backbone/backbone-full": require_base+"/libs/backbone/backbone-full",
		//"../jquery-ui-1.8.21.custom.min": "media/js/jquery-ui-1.8.21.custom.min",
		
	},
};
