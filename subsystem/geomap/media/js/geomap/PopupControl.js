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

PopupControl = OpenLayers.Class(OpenLayers.Control, {

    layer: null,

    popups: null,

    mousePos: {x:0,y:0},

    initialize: function(layer, options) {
	OpenLayers.Control.prototype.initialize.apply(this, [options]);
	this.layer = layer;
	this.popups = {};

	var callbacks = {
	    'click': this.clickFeature,
	    'over': this.overFeature,
	    'out': this.outOfFeature
	};
        
	this.handler = new OpenLayers.Handler.Feature(this, this.layer, callbacks);
    },

    setMap: function(map) {
	OpenLayers.Control.prototype.setMap.apply(this, arguments);
	this.map.events.register('mousemove', this, this.mouseMoved);
    },


    mouseMoved: function(event) {
	this.mousePos = this.map.events.getMousePosition(event);
    },
    

    clickFeature: function(feature) {
	setOutput('CLICK ' + feature.data.name);
	this.showPopup(this.getPopup(feature.data.popup));
    },

    overFeature: function(feature) {
	setOutput('OVER ' + feature.data.name);
	if (feature.data.miniPopup == null) return;
	clearTimeout(feature.data.miniPopupTimeout);
	if (!feature.data.miniPopup.visible()) {
	    var t = this;
	    feature.data.miniPopup.div.onmouseover = function() {
		feature.data.miniPopup.mouseover = true;
		clearTimeout(feature.data.miniPopupTimeout);
	    };
	    feature.data.miniPopup.div.onmouseout = function() {
		feature.data.miniPopup.mouseover = false;
		var hide = function() { t.hidePopup(feature.data.miniPopup); };
		feature.data.miniPopupTimeout = setTimeout(hide, 100);
		//t.hidePopup(feature.data.miniPopup);
	    };
	    this.showPopup(feature.data.miniPopup);
	}
    },

    outOfFeature: function(feature) {
	setOutput('nothing');
	if (feature.data.miniPopup == null) return;
	var t = this;
	var hide = function() { t.hidePopup(feature.data.miniPopup); };
	feature.data.miniPopupTimeout = setTimeout(hide, 300);
	/*
		if (!feature.data.miniPopup.mouseover)
			this.hidePopup(feature.data.miniPopup);
		*/
    },


    getPopup: function(popupData) {
	if (!popupData)
	    return null;

	var popup;
	var id = popupData.id;

	if (popup = this.popups[id])
	    return popup;

	// set (0,0) as position now; will set correct position when
	// popup is shown:
	var pos = new OpenLayers.LonLat(0, 0);
	var size = new OpenLayers.Size(popupData.size[0], popupData.size[1]);
	var content = popupData.content;
	var closable = popupData.closable;
	var anchor = {'size': new OpenLayers.Size(0,0),
		      'offset': new OpenLayers.Pixel(0,0)};

	var popupclass = OpenLayers.Popup.AnchoredBubble;
	popupclass= OpenLayers.Popup.FramedCloud;
	popup = new popupclass(id, pos, size, content, anchor, closable);
	popup.maxSize = size;
	popup.autoSize = true;
	this.popups[id] = popup;
	return popup;
    },

    showPopup: function(popup) {
	if (!popup) return;
	popup.lonlat = this.map.getLonLatFromPixel(this.mousePos);
	this.map.removePopup(popup);
	this.map.addPopup(popup);
	popup.show();
    },

    hidePopup: function(popup) {
	if (popup) popup.hide();
    },

    CLASS_NAME: "PopupControl"

});



function setOutput(str) {
    //document.getElementById("output").firstChild.nodeValue = str;
}
