/* -*- coding: utf-8 -*-
 *
 * Threshold specific javascripts
 *
 * Copyright (C) 2012 UNINETT AS
 *
 * This file is part of Network Administration Visualized (NAV).
 *
 * NAV is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License version 2 as published by
 * the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.  You should have received a copy of the GNU General Public
 * License along with NAV. If not, see <http://www.gnu.org/licenses/>.
 *
 */

require(['libs/jquery', 'libs/jquery-json-2.2.min', 'libs/spin.min'], function () {
    $(function () {
        if(!Array.indexOf){
            Array.prototype.indexOf = function(obj){
                for(var i=0; i<this.length; i++){
                    if(this[i]==obj){
                        return i;
                    }
                }
                return -1;
            }
        }

        /*
         * A simple timer-function that will call the given "callback"
         * after a timeout(given in millisecs).
         */
        var typeDelay = function(){
            var timer = 0;
            return function(callback, ms){
                clearTimeout (timer);
                timer = setTimeout(callback, ms);
            }
        }(); /* typeDelay */

        /*
         * Implements a <div> with the spinning wheel.
         */
        $.fn.spin = function(opts) {
            this.each(function() {
                var $this = $(this),
                    spinner = $this.data('spinner');

                if (spinner){
                    spinner.stop();
                }
                if (opts !== false) {
                    spinner = new Spinner($.extend({color: $this.css('color')}, opts)).spin(this);
                    $this.data('spinner', spinner);
                }
            });
            return this;
        }; /* $.fn.spin */

        /*
         * Declare a separate namespace for all variables and functions related to
         * the threshold-webpages.
         */
        var threshold = threshold || {};

        /* Used as a semaphore to block out concurrent ajax-calls to netbox-search. */
        threshold.netboxSearchReq = null;
        /* Used as a semaphore to block out concurrent ajax-calls to bulkset */
        threshold.getBulkUpdateHtmlReq = null;
        /* Used as a semaphore to block out concurrent ajax-calls to chooseDevice */
        threshold.chooseDeviceTypeReq = null;
        /* Used as a semaphore to block out concurrent ajax-calls to saveToServer */
        threshold.saveToServerReq = null;

        /* netbox- or interface-mode */
        threshold.displayMode = '';

        threshold.stdErrColor = 'red';
        threshold.stdSuccessColor = 'green';
        threshold.perCentRepl = new RegExp('%*$');
        threshold.descriptionRegExp = new RegExp('^[a-zA-Z0-9][a-zA-Z0-9\ ]+$');

        threshold.spinnerOptions = {
            lines: 14, // The number of lines to draw
            length: 20, // The length of each line
            width: 10, // The line thickness
            radius: 22, // The radius of the inner circle
            rotate: 0, // The rotation offset
            color: '#020202', // #rgb or #rrggbb
            speed: 1, // Rounds per second
            trail: 50, // Afterglow percentage
            shadow: false, // Whether to render a shadow
            hwaccel: false, // Whether to use hardware acceleration
            className: 'spinner', // The CSS class to assign to the spinner
            zIndex: 2e9 // The z-index (defaults to 2000000000)
        };


        threshold.backToSearch = function(){
            $('#netboxsearch').show();
            if(threshold.displayMode == 'interface'){
                $('#interfacesearch').show();
            }
            var bulkUpdateData = $('#bulkupdateDiv');
            $(bulkUpdateData).hide();
            $(bulkUpdateData).empty();
            threshold.removeMessages();
        }; /* backToSearch */


        threshold.removeMessages = function(){
            var messagesDiv = $('#messagesDiv');
            $(messagesDiv).empty();
        }; /* removeMessages */


        threshold.updateMessages = function(msg, isError){
            var messagesDiv = $('#messagesDiv');
            $(messagesDiv).append('<ul><li>' + msg + '</li></ul>');
            if(isError){
                $(messagesDiv).css('color', threshold.stdErrColor);
            } else {
                $(messagesDiv).css('color', threshold.stdSuccessColor);
            }
        }; /* updateMessages */


        threshold.pageNotFound = function(){
            threshold.updateMessages('Page not found', true);
        }; /* pageNotFound */


        threshold.serverError = function(){
            threshold.updateMessages('Internal server-error', true);
        }; /* serverError */


        threshold.ajaxError = function( request, errMessage, errType){
            var errMsg = 'Error: ' + errMessage + '; ' + errType;
            threshold.updateMessages(errMsg, true);
        }; /* ajaxError */


        threshold.isLegalDescription = function(desc){
            return desc.match(threshold.descriptionRegExp);
        }; /* isLegalDescription */


        /*
         * Takes a table and makes it a string.  Each element from the table
         * is separated with the character "|" in the string.
         */
        threshold.table2String = function(tab){
            var len = tab.length;
            var ret_str = '';
            for(var i = 0; i < len; i++){
                if(i > 0 ){
                    ret_str += '|';
                }
                ret_str += tab[i];
            }
            return ret_str;
        }; /* table2String */


        threshold.toggleIncludes = function(checkbox){
            if( $(checkbox).prop('checked') ){
                threshold.checkAllInclude();
            } else {
                threshold.unCheckAllInclude();
            }
        }; /* toggleIncludes */


        threshold.checkAllInclude = function(){
            var allIncludes = $("#bulkUpdateTable input.includeInBulk") || [];
            for(var i = 0; i < allIncludes.length; i++){
                $(allIncludes[i]).prop('checked', true);
            }
        }; /* checkAllInclude */


        threshold.unCheckAllInclude = function(){
            var allIncludes = $("#bulkUpdateTable input.includeInBulk:checked") || [];
            for(var i = 0; i < allIncludes.length; i++){
                $(allIncludes[i]).prop('checked', false);
            }
        }; /* unCheckAllInclude */


        threshold.stripPerCentSymbol = function(str){
            return str.replace(threshold.perCentRepl, '');
        }; /* stripPerCentSymbol */


        /*
         * NB!
         * Always remember to keep error-chekcing here and on server in sync!
         */
        threshold.isLegalThreshold = function(thr){
            if( thr.length == 0){
                return true;
            }
            var intValue = parseInt(threshold.stripPerCentSymbol(thr));
            return (! isNaN(intValue));
        }; /* isLegalThreshold */


        threshold.setThresholdInputClass = function(thrInput, className){
            var thrParent = $(thrInput).parent();
            $(thrParent).removeClass();
            $(thrParent).addClass(className);
        } /* setThresholdInputClass */


        threshold.setChangedThreshold = function(thrInput){
            threshold.setThresholdInputClass(thrInput, 'changed');
        }; /* setChangedThreshold */


        threshold.showSavedThreshold = function(thrInput){
            threshold.setThresholdInputClass(thrInput, 'success');
        }; /* showSavedThreshold */


        threshold.showErrorThreshold = function(thrInput){
            threshold.setThresholdInputClass(thrInput, 'error');
        }; /* showErrorThreshold */


        threshold.netboxSearch = function(){
            threshold.removeMessages();
            if(threshold.netboxSearchReq) {
                /* The previous ajax-call is cancelled and replaced with the last */
                threshold.netboxSearchReq.abort();
            }
            var descr = $('#thresholdDescr').val();
            var sysname = $('#netboxSysname').val();
            // The checkboxes for GW, GSW and SW
            var checkBoxList = $('input:checkbox[name="boxtype"]:checked') || [];
            var vendor = $('#boxVendor').val();
            var model = $('#netBoxModel').val();
            var ifname = $('#interfaceName').val();
            var upDown = $('input:checkbox[name="interfaceUpDown"]:checked').val();

            var boxes = $('#chosenBoxes').val() || [];

            if(descr == 'empty'){
                return -1;
            }
            if(! threshold.isLegalDescription(descr)){
                threshold.updateMessages('Illegal threshold description', true);
                return -1;
            }
            var inputData = { 'descr': descr };

            if(sysname.length > 0){
                inputData['sysname'] = sysname;
            }

            if(vendor != 'empty'){
                inputData['vendor'] = vendor;
            }
            if(model != 'empty'){
                inputData['model'] = model;
            }

            if(ifname.length > 0){
                inputData['ifname'] = ifname;
            }

            if(upDown == 'updown'){
                inputData['updown'] = upDown;
            }

            var chosenboxes = ''
            if(boxes.length > 0 ){
                inputData['boxes'] = threshold.table2String(boxes);
            }

            for(var i = 0; i < checkBoxList.length; i++){
                inputData[$(checkBoxList[i]).val()] = $(checkBoxList[i]).val();
            }
            $('div.spinnerContainer').spin(threshold.spinnerOptions);
            threshold.netboxSearchReq =
                $.ajax({ url: '/threshold/netboxsearch/',
                    data: inputData,
                    dataType: 'json',
                    type: 'POST',
                    async: true,
                    timeout: 180000,
                    success:   function(data, textStatus, header){
                        if(data.error){
                            threshold.updateMessages(data.message, true);
                            return -1;
                        }
                        $('#chosenBoxes').empty();
                        $('#chosenBoxes').append(data.foundboxes);
                        $('#choseninterfaces').empty();
                        $('#choseninterfaces').append(data.foundinterfaces);
                        if(data.types){
                            $('#netBoxModel').empty();
                            $('#netBoxModel').append(data.types);
                        }
                        return 0;
                    },
                    error:     function(req, errMsg, errType){
                        /*
                         threshold.ajaxError(req, errMsg, errType);
                         */
                        threshold.netboxSearchReq = null;
                        return -1;
                    },
                    complete:  function(header, textStatus){
                        $('div.spinnerContainer').spin(false);
                        threshold.netboxSearchReq = null;
                        return 0;
                    },
                    statusCode: { 404: function(){
                        threshold.pageNotFound();
                        threshold.netboxSearchReq = null;
                        return -1;
                    },
                        500: function(){
                            threshold.serverError();
                            threshold.netboxSearchReq = null;
                            return -1;
                        }
                    }
                });
            return 0;
        }; /* netboxSearch */


        threshold.getBulkUpdateHtml = function(descr, ids){
            threshold.removeMessages();
            if(threshold.getBulkUpdateHtmlReq){
                /* The previous ajax-call is cancelled and replaced with the last */
                threshold.getBulkUpdateHtmlReq.abort();
            }
            if(! threshold.isLegalDescription(descr)){
                threshold.updateMessages('Illegal threshold description', true);
                return -1;
            }
            var inputData = {
                'descr': descr,
                'ids': ids
            };
            $('div.spinnerContainer').spin(threshold.spinnerOptions);
            threshold.getBulkUpdateHtmlReq =
                $.ajax({url: '/threshold/preparebulk/',
                    data: inputData,
                    dataType: 'text',
                    type: 'POST',
                    async: true,
                    timeout: 180000,
                    success:    function(data, textStatus, header){
                        if(data.error){
                            threshold.updateMessages(data.message, true);
                            return -1;
                        }
                        $('#netboxsearch').hide();
                        $('#interfacesearch').hide();
                        $('#bulkupdateDiv').show();
                        $('#bulkupdateDiv').html(data);
                        threshold.attachBulkListeners();
                        return 0;
                    },
                    error:      function(req, errMsg, errType){
                        /*
                         threshold.ajaxError(req, errMsg, errType);
                         */
                        threshold.getBulkUpdateHtmlReq = null;
                        return -1;
                    },
                    complete:   function(header, textStatus){
                        $('div.spinnerContainer').spin(false);
                        threshold.getBulkUpdateHtmlReq = null;
                        return 0;
                    },
                    statusCode: { 404:  function(){
                        threshold.pageNotFound();
                        threshold.getBulkUpdateHtmlReq = null;
                        return -1;
                    },
                        500:   function(){
                            threshold.serverError();
                            threshold.getBulkUpdateHtmlReq = null;
                            return -1;
                        }
                    }
                });
            return 0;
        }; /* getBulkUpdateHtml */

        threshold.chooseDeviceType = function(the_select, select_val){
            threshold.removeMessages();
            if(threshold.chooseDeviceTypeReq){
                /* The previous ajax-call is cancelled and replaced with the last */
                threshold.chooseDeviceTypeReq.abort();
            }
            $('div.spinnerContainer').spin(threshold.spinnerOptions);
            threshold.chooseDeviceTypeReq =
                $.ajax({url: '/threshold/choosetype/',
                    data: {'descr': select_val},
                    dataType: 'json',
                    type: 'POST',
                    async: true,
                    timeout: 180000,
                    success:    function(data, textStatus, header){
                        if(data.error){
                            threshold.updateMessages(data.Message, true);
                            return -1;
                        }
                        threshold.displayMode = data.message;
                        threshold.netboxSearch();
                        if(threshold.displayMode == 'interface'){
                            $('#netboxSubmitDiv').hide();
                            $('#netboxsearch').show();
                            $('#interfacesearch').show();
                            $('#interfaceSubmitDiv').show();
                        }
                        if(threshold.displayMode == 'netbox'){
                            $('#interfaceSubmitDiv').hide();
                            $('#interfacesearch').hide();
                            $('#netboxsearch').show();
                            $('#netboxSubmitDiv').show();
                        }
                        return 0;
                    },
                    error:      function(req, errMsg, errType){
                        /*
                         threshold.ajaxError(req, errMsg, errType);
                         */
                        threshold.chooseDeviceTypeReq = null;
                        return -1;
                    },
                    complete:   function(header, textStatus){
                        $('div.spinnerContainer').spin(false);
                        threshold.chooseDeviceTypeReq = null;
                        return 0;
                    },
                    statusCode: { 404:  function(){
                        threshold.pageNotFound();
                        threshold.chooseDeviceTypeReq = null;
                        return -1;
                    },
                        500:   function(){
                            threshold.serverError();
                            threshold.chooseDeviceTypeReq = null;
                            return -1;
                        }
                    }
                });
            return 0;
        }; /* chooseDeviceType */


        threshold.saveToServer = function(toSave, chosenIds, parentTable){
            threshold.removeMessages();
            if(threshold.saveToServerReq){
                threshold.saveToServerReq.abort();
            }
            var objectJSON = $.toJSON(toSave);
            $('div.spinnerContainer').spin(threshold.spinnerOptions);
            threshold.saveToServerReq =
                $.ajax({url: '/threshold/thresholdssave/',
                    data: {'thresholds': objectJSON},
                    dataType: 'json',
                    type: 'POST',
                    async: true,
                    timeout: 180000,
                    success:    function(data, textStatus, header){
                        var serverMsg = null;
                        var isErrors = false;
                        if((data.error) && (data.error > 0)){
                            if(data.failed.length > 0 ){
                                serverMsg = data;
                                isErrors = true;
                            } else {
                                serverMsg = {};
                                serverMsg.message = 'Save failed'
                                serverMsg.failed = chosenIds.slice();
                                serverMsg.error = serverMsg.failed.length;
                                isErrors = true;
                            }
                        }
                        if(isErrors){
                            threshold.updateMessages(serverMsg.message, true);
                            for(var i = 0; i < serverMsg.failed.length; i++){
                                var dsId = serverMsg.failed[i];
                                var row = $("tr." + dsId, parentTable);
                                var thrInput = $('input:text.threshold', row);
                                threshold.showErrorThreshold(thrInput);
                                /* Remove those who did not get saved */
                                var idx = chosenIds.indexOf(dsId);
                                if(idx > -1){
                                    chosenIds.splice(idx, 1);
                                }
                            }
                        }
                        for(var i = 0; i < chosenIds.length; i++){
                            var dsId = chosenIds[i];
                            var row = $("tr." + dsId, parentTable);
                            var thrInput = $('input:text.threshold', row);
                            threshold.showSavedThreshold(thrInput);
                        }
                        return 0;
                    },
                    error:      function(req, errMsg, errType){
                        /*
                         threshold.ajaxError(req, errMsg, errType);
                         */
                        threshold.saveToServerReq = null;
                        return -1;
                    },
                    complete:   function(header, textStatus){
                        $('div.spinnerContainer').spin(false);
                        threshold.saveToServerReq = null;
                        return 0;
                    },
                    statusCode: { 404:  function(){
                        threshold.pageNotFound();
                        threshold.saveToServerReq = null;
                        return -1;
                    },
                        500:  function(){
                            threshold.serverError();
                            threshold.saveToServerReq = null;
                            return -1;
                        }
                    }

                });
            return 0;
        }; /* saveToServer */


        threshold.saveChosenThresholds = function(allIncludes){
            /* Save for later use */
            var bulkUpdateTable = $('#bulkUpdateTable');
            /* Holds an dict of id, operator and threshold-value */
            var thresholdsToSave = new Array();
            /* An array with ids to update the GUI */
            var chosenIds = new Array();
            for(var i = 0; i < allIncludes.length; i++){
                var chkbox = allIncludes[i];
                var row = $(chkbox).parent().parent();
                var dsId = $(row).attr('class');
                var op = $('select.operator', row).val();
                var thrInput = $('input:text.threshold', row);
                var thrVal = $(thrInput).val();
                var units = $('select.unit', row).val();
                if((thrVal.length > 0) && (units == '%')){
                    thrVal += '%';
                }
                thresholdsToSave[i] = {'dsId' : dsId, 'op': op, 'thrVal': thrVal};
                chosenIds[i] = dsId;
            }
            threshold.saveToServer(thresholdsToSave, chosenIds, bulkUpdateTable);
            return 0;
        }; /* saveChosenThresholds */


        threshold.saveSingleThreshold = function(btn){
            threshold.removeMessages();
            var row = $(btn).parent().parent();
            var thrInput = $('input:text.threshold', row);
            var thrVal = $(thrInput).val();
            if(! threshold.isLegalThreshold(thrVal)){
                threshold.updateMessages('Save failed. Illegal threshold', true);
                threshold.showErrorThreshold(thrInput);
                return -1;
            }

            var chkbox= $('input:checkbox.includeInBulk', row);
            threshold.saveChosenThresholds([chkbox]);
            return 0;
        }; /* saveSingleThreshold */


        threshold.saveCheckedThresholds = function(){
            threshold.removeMessages();
            var bulkUpdateTable = $('#bulkUpdateTable');
            var allIncludes = $('input.includeInBulk:checked', bulkUpdateTable) || [];
            if(allIncludes.length < 1){
                threshold.updateMessages('Please, check the ones to save', true);
                return -1;
            }
            threshold.saveChosenThresholds(allIncludes);
            return 0;
        }; /* saveCheckedThresholds */


        threshold.clearCheckedThresholds = function(){
            threshold.removeMessages();
            var bulkUpdateTable = $('#bulkUpdateTable');
            var allIncludes = $('input.includeInBulk:checked', bulkUpdateTable) || [];
            for( var i = 0; i < allIncludes.length; i++){
                var row = $(allIncludes[i]).parent().parent();
                var thrInput = $('input:text.threshold', row);
                if($(thrInput).val().length > 0 ){
                    $(thrInput).val('');
                    threshold.setChangedThreshold(thrInput);
                } else {
                    $(thrInput).parent().removeClass();
                }
            }
        };


        threshold.saveAllThresholds = function(){
            var bulkUpdateTable = $('#bulkUpdateTable');
            var allIncludes = $('input:checkbox.includeInBulk', bulkUpdateTable) || [];
            if(allIncludes.length < 1){
                return -1;
            }
            threshold.saveChosenThresholds(allIncludes);
            return 0;
        }; /* saveAllThresholds */


        threshold.clearAllThresholds = function(){
            threshold.removeMessages();
            var bulkUpdateTable = $('#bulkUpdateTable');
            var allThresholds = $('input:text.threshold', bulkUpdateTable) || [];
            for(var i = 0; i < allThresholds.length; i++){
                var thrInput = allThresholds[i];
                if($(thrInput).val().length > 0 ){
                    $(thrInput).val('');
                    threshold.setChangedThreshold(thrInput);
                } else {
                    $(thrInput).parent().removeClass();
                }
            }
        }; /* clearAllThresholds */


        threshold.bulkUpdateThresholds = function(){
            threshold.removeMessages();
            var bulkSetTable = $('#bulkSetTable');
            var bulkRow = $("tr", bulkSetTable);
            var bulkOperator = $("select", bulkRow).val();
            var bulkThrInput = $("input:text", bulkRow);
            var bulkThr= $(bulkThrInput).val();
            if(! threshold.isLegalThreshold(bulkThr)){
                threshold.updateMessages('Illegal threshold', true);
                threshold.showErrorThreshold(bulkThrInput);
                return -1;
            }
            var thrAsPerCent = $("input:checkbox", bulkRow).prop('checked');

            /* Start updating the bulk-table */
            var bulkUpdateTable = $('#bulkUpdateTable');
            var allIncludes = $('input.includeInBulk:checked', bulkUpdateTable) || [];
            if(allIncludes.length < 1){
                threshold.updateMessages('Please, check the ones to update', true);
                return -1;
            }

            $(bulkThrInput).parent().removeClass();
            for(var i = 0; i < allIncludes.length; i++){
                var chkbox = allIncludes[i];
                var row = $(chkbox).parent().parent();
                var thresholdOperator = $("select.operator", row);
                $(thresholdOperator).val(bulkOperator);
                var thrInput = $("input:text.threshold", row);
                $(thrInput).val(bulkThr);
                // Mark as changed
                threshold.setChangedThreshold(thrInput);
                var unitsSelect = $("select.unit", row);
                if( unitsSelect != null ){
                    if(thrAsPerCent){
                        $(unitsSelect).val('%');
                    } else {
                        if( $(unitsSelect).val() == '%'){
                            /* Reset select to first value */
                            var firstValue = $('select.unit', row).find('option:first').val();
                            $(unitsSelect).val(firstValue);
                        }
                    }
                }
            }
        }; /* bulkUpdateThresholds */


        threshold.attachBulkListeners = function(){
            $('#bulkSetTable input:button').click(threshold.bulkUpdateThresholds);

            var bulkUpdateTable = $('#bulkUpdateTable');

            $('input.toggleIncludes', bulkUpdateTable).change(function(){
                threshold.toggleIncludes(this);
            });

            $('input.threshold', bulkUpdateTable).change(function(){
                threshold.setChangedThreshold(this);
            });

            $(bulkUpdateTable).find('input.button').each(function(){
                $(this).click(function(){
                    var row = $(this).parent().parent();
                    var dsId = $(row).attr('class');
                    var parentTable = $(row).parent();
                    var thrVal = $('input:text.threshold', row).val();
                    var op = $('select.operator', row).val();
                    var unit = $('select.unit', row).val();
                    if((thrVal.length > 0) && (unit == '%')){
                        thrVal += '%';
                    }
                    var toSave = {'dsId': dsId, 'op': op, 'thrVal': thrVal};
                    threshold.saveToServer([toSave], [dsId], parentTable);
                });
            });

            $("#saveCheckedThresholdsTop").click(threshold.saveCheckedThresholds);
            $('#clearCheckedThresholdsTop').click(threshold.clearCheckedThresholds);

            $("#saveAllThresholdsTop").click(threshold.saveAllThresholds);
            $('#clearAllThresholdsTop').click(threshold.clearAllThresholds);

            $("#saveCheckedThresholdsBottom").click(threshold.saveCheckedThresholds);
            $("#clearCheckedThresholdsBottom").click(threshold.clearCheckedThresholds);

            $("#saveAllThresholdsBottom").click(threshold.saveAllThresholds);
            $('#clearAllThresholdsBottom').click(threshold.clearAllThresholds);

        }; /* attachBulkListeners */


        $(document).ready(function(){
            NAV.addGlobalAjaxHandlers();
            $('#thresholdDescr').change(function(){
                threshold.removeMessages();
                var sval = $(this).val();
                if(sval == 'empty'){
                    return -1;
                }
                if(! threshold.isLegalDescription(sval)){
                    threshold.updateMessages('Illegal threshold description', true);
                    return -1;
                }
                $('#bulkupdateDiv').hide();
                threshold.chooseDeviceType(this, sval);
            });

            $('#netboxSysname').keyup(function(){
                typeDelay(function(){
                    threshold.netboxSearch();
                }, 500);
            });

            $('input:checkbox').change(function(){
                threshold.netboxSearch();
            });

            $('#boxVendor').change(function(){
                threshold.netboxSearch();
            });

            $('#netBoxModel').change(function(){
                threshold.netboxSearch();
            });

            $('#chosenBoxes').change(function(){
                if(threshold.displayMode == 'interface'){
                    threshold.netboxSearch();
                }
            });

            $('#interfaceName').keyup(function(){
                typeDelay(function(){
                    threshold.netboxSearch();
                }, 500);
            });

            $('#netboxSubmit').click(function(){
                threshold.removeMessages();
                var thresholdDescr = $('#thresholdDescr').val();
                var chosenBoxes = $('#chosenBoxes').val() || [];
                if(chosenBoxes.length > 0){
                    threshold.getBulkUpdateHtml(thresholdDescr, threshold.table2String(chosenBoxes));
                } else {
                    threshold.updateMessages('No netboxes chosen', true);
                    return -1;
                }
                return 0;
            });

            $('#interfaceSubmit').click(function(){
                threshold.removeMessages();
                var descr = $('#thresholdDescr').val();
                var interfaces = $('#choseninterfaces').val() || [];
                if(interfaces.length > 0){
                    threshold.getBulkUpdateHtml(descr, threshold.table2String(interfaces));
                } else {
                    threshold.updateMessages('No interfaces chosen', true);
                    return -1;
                }
                return 0;
            });

            $('img.toggler').click(function(){
                var parent = $(this).parent();
                var images = $('img', parent) || [];
                for(var i = 0; i < images.length; i++){
                    $(images[i]).toggle();
                }
                $(this).parent().parent().find('table.vertitable').toggle();
            });

            $('div.netboxcontainer').find('input.button').each(function(){
                $(this).click(function(){
                    var row = $(this).parent().parent();
                    var dsId = $(row).attr('class');
                    var parentTable = $(row).parent();
                    var thrVal = $('input:text.threshold', row).val();
                    var op = $('select.operator', row).val();
                    var unit = $('select.unit', row).val();
                    if((thrVal.length > 0) && (unit == '%')){
                        thrVal += '%';
                    }
                    var toSave = {'dsId': dsId, 'op': op, 'thrVal': thrVal};
                    threshold.saveToServer([toSave], [dsId], parentTable);
                });
            });

            $('input.threshold').change(function(){
                threshold.setChangedThreshold(this);
            });
        });
    });
});
