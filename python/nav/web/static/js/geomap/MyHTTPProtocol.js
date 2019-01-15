/*
 * Copyright (C) 2009, 2010 Uninett AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License version 3 as published by the Free
 * Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * Small extension of OpenLayers.Protocol.HTTP providing "dynamic
 * parameters".  These are like the params property of O.P.HTTP except
 * that they are not fixed at the time the Protocol object is
 * constructed.  Instead, they are specified by functions which are
 * called each time the parameters are needed.
 *
 * Dynamic parameters are specified by setting dynamicParams in the
 * options argument to the constructor.
 */
MyHTTPProtocol = OpenLayers.Class(OpenLayers.Protocol.HTTP, {

    /*
     * Dynamic parameters, dictionary mapping parameter names to
     * functions.  (The functions should take no arguments).
     */
    dynamicParams: null,

    /*
     * Overrides the read function of OpenLayers.Protocol.HTTP.
     */
    read: function(options) {
	var dynamicParams = this.evaluateDynamicParams();
	var params = extend(this.params,
			    extend(options.params, dynamicParams));
	var extOptions = extend(options, {params: params});
	return OpenLayers.Protocol.HTTP.prototype.read.apply(this,
							     [extOptions]);
    },

    /*
     * Evaluate the dynamic parameters.
     *
     * Returns a dictionary with parameter names mapped to parameter
     * values (results of calling the functions in dynamicParams).
     */
    evaluateDynamicParams: function() {
	var params = {};
	for (var key in this.dynamicParams)
	    params[key] = this.dynamicParams[key]();
	return params;
    },
    
    CLASS_NAME: "MyHTTPProtocol"
});    
