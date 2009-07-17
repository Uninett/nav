/*
 * Copyright (C) 2009 UNINETT AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 */

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
