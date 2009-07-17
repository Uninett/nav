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

/*
 * Permalink.js: Maintains a link such that it always points to a page
 * with the current configuration.
 */

function Permalink(htmlId, mapObj, parameters, listenHooks) {
    this.htmlId = htmlId;
    this.map = mapObj;
    this.permalinkControl = new OpenLayers.Control.Permalink(
	{draw: function(){}});
    mapObj.addControl(this.permalinkControl);
    this.parameters = parameters;

    var queryString = OpenLayers.Util.getParameters();
    for (var i in parameters)
	if (i in queryString)
	    parameters[i] = queryString[i];

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

