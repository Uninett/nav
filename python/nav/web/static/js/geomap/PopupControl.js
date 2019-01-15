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
 * OpenLayers control for opening popups when clicking on features.
 *
 * In order to get a popup, a feature f must have a f.data.popup with
 * the following properties:
 *
 *  id -- identifier of the popup; must be unique among the features
 *  content -- HTML content for the popup
 *
 * A popup is always shown at the point where the mouse was clicked.
 * If the popup for a feature is already open and the feature is
 * clicked again, the popup is closed and then reopened at the
 * position of the second click.
 */
PopupControl = OpenLayers.Class(OpenLayers.Control, {

    /*
     * The layer this control belongs to.
     */ 
    layer: null,

    /*
     * Dictionary of generated popups indexed by id.
     */
    popups: null,

    /*
     * The position of the last mouse click (used for positioning
     * popups).
     */
    mousePos: {x:0,y:0},

    initialize: function(layer, options) {
	OpenLayers.Control.prototype.initialize.apply(this, [options]);
	this.layer = layer;
	this.popups = {};

	var callbacks = {
        'click': this.clickFeature
	};

	this.handler = new OpenLayers.Handler.Feature(this, this.layer, callbacks);
    },

    setMap: function(map) {
	OpenLayers.Control.prototype.setMap.apply(this, arguments);
	this.map.events.register('mousemove', this, this.mouseMoved);
    },

    /*
     * Callback function for mouse movement.
     */
    mouseMoved: function(event) {
	this.mousePos = this.map.events.getMousePosition(event);
    },
    
    /*
     * Callback function for 'mouse click on a feature' events.
     */
    clickFeature: function(feature) {
	this.showPopup(feature.data.popup);
    },

    /*
     * Get a previously created popup object for some popup data.
     */
    getPopup: function(popupData) {
	if (!popupData)
	    return null;
	return this.popups[popupData.id];
    },

    /*
     * Create a new popup object for the given popup data.
     */
    makePopup: function(popupData) {
	var id = popupData.id;
	// set (0,0) as position now; will set correct position when
	// popup is shown:
	var pos = new OpenLayers.LonLat(0, 0);
	var size = new OpenLayers.Size(popupData.size[0], popupData.size[1]);
	var content = popupData.content;
	var closable = popupData.closable;
	var anchor = {'size': new OpenLayers.Size(0,0),
		      'offset': new OpenLayers.Pixel(0,0)};

	var popupclass = OpenLayers.Popup.AnchoredBubble;
	var popup = new popupclass(id, pos, size, content, anchor, closable);
	//popup.maxSize = size;
	popup.autoSize = true;
	this.popups[id] = popup;
	return popup;
    },

    /*
     * Show a popup.
     */
    showPopup: function(popupData) {
	if (!popupData) return;
	var existingPopup = this.getPopup(popupData);
	if (existingPopup)
	    this.map.removePopup(existingPopup);
	var newPopup = this.makePopup(popupData);
	newPopup.lonlat = this.map.getLonLatFromPixel(this.mousePos);
	this.map.addPopup(newPopup);
	newPopup.show();
    },

    /*
     * Hide a popup.
     */
    hidePopup: function(popup) {
	if (popup) popup.hide();
    },

    CLASS_NAME: "PopupControl"

});
