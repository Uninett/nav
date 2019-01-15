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
 * Permalink.js: Maintains a link such that it always points to a page
 * with the current configuration.
 *
 * Uses OpenLayers.Control.Permalink for permalinking the
 * position/zoom and visible layers in the map, and allows the user to
 * add arbitrary extra parameters.  Takes care of both setting values
 * from the query string and creating a link containing the current
 * values.
 *
 * The parameters argument to the constructor specifies how the extra
 * parameters are read and written.  To make the link get updated when
 * the values change, the user of this class may either call the
 * update function on each change, or specify the listenHooks argument
 * to the constructor.
 *
 * Unlike OpenLayers.Control.Permalink, Permalink objects show the
 * link with a HTML element outside the map.
 */

/*
 * Constructor.
 *
 * Arguments:
 *
 * htmlId -- id of HTML element (should be an A element) for the link.
 * The HREF attribute of this element is controlled by the Permalink
 * object, it is otherwise left as it is.
 *
 * mapObj -- the map object (instance of OpenLayers.Map)
 *
 * parameters -- additional parameters to use in the link (parameters
 * encoding map position/zoom and what layers are visible are
 * automatically included).  The property names of this object are
 * used as parameter names and the corresponding values as parameter
 * values.  If any of these names are specified in the query string of
 * the URL of the page being shown, the values from the query string
 * are written into the parameters object.  All values in the
 * parameters object are read each time the permalink is
 * reconstructed.  (Tip: specifying the properties of the parameters
 * object with getters and setters may be very useful).
 *
 * listenHooks -- array of hooks (see util.js) which should cause the
 * link to be updated.  The Permalink object will add a function to
 * each of these hooks.
 */
function Permalink(htmlId, mapObj, parameters, listenHooks) {
    this.htmlId = htmlId;
    this.map = mapObj;
    this.permalinkControl = new OpenLayers.Control.Permalink(
	{draw: function(){}});
    mapObj.addControl(this.permalinkControl);
    this.parameters = parameters;

    var queryString = OpenLayers.Util.getParameters();
    for (var i in parameters) {
        if (i in queryString) {
            parameters[i] = queryString[i];
        }
    }

    if (listenHooks)
	listenHooks.forEach(fix(addHook, encapsulate(this, this.update), 1));
    mapObj.events.register('moveend', this, this.update);

    this.update();
}

Permalink.prototype = {
    htmlId: null,
    map: null,
    permalinkControl: null,

    getURL: function() {
	return document.location.pathname + '?' + this.getQueryString();
    },

    getQueryString: function() {
	return OpenLayers.Util.getParameterString(this.getParameters());
    },

    getParameters: function() {
	return extend(this.parameters, this.permalinkControl.createParams());
    },

    update: function() {
	var elem = document.getElementById(this.htmlId);
	elem.setAttribute('href', this.getURL());
    },

    toString: function() {
	return format('<Permalink "%s">', this.htmlId);
    }

};

