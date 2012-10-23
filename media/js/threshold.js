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
}();

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
/* netbox- or interface-mode */
threshold.displayMode = '';
threshold.stdBgColor = 'white';
threshold.stdErrColor = 'red';
threshold.stdSuccessColor = 'green';
threshold.perCentRepl = new RegExp('%*$');
threshold.descriptionRegExp = new RegExp('^[a-zA-Z][a-zA-Z0-9\ ]+$');
threshold.thresholdSaveStatus = 0;
threshold.saveMessage = null;

/*
 * Kind of a semaphore to block out concurrent ajax-calls for
 * save_threshold.
*/
threshold.save_queue =  new Array();

threshold.removeFromQueue = function(id){
    var idx = threshold.save_queue.indexOf(id);
    if(idx > -1){
	threshold.save_queue.splice(idx, 1);
    }
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
};

threshold.removeMessages = function(){
    var messagesDiv = $('#messagesDiv');
    $(messagesDiv).empty();
};

threshold.updateMessages = function(msg, isError){
    var messagesDiv = $('#messagesDiv');
    $(messagesDiv).append('<ul><li>' + msg + '</li></ul>');
    if(isError){
        $(messagesDiv).css('color', threshold.stdErrColor);
    } else {
        $(messagesDiv).css('color', threshold.stdSuccessColor);
    }
};

threshold.pageNotFound = function(){
    threshold.updateMessages('Page not found', true);
    return -1;
};

threshold.serverError = function(){
    threshold.updateMessages('Internal server-error', true);
    return -1;
};

threshold.ajaxError = function( request, errMessage, errType){
    var errMsg = 'Error: ' + errMessage + '; ' + errType;
    threshold.updateMessages(errMsg, true);
    return -1;
};

threshold.isLegalDescription = function(desc){
    return desc.match(threshold.descriptionRegExp);
};

threshold.showAjaxLoader = function(){
    $('span.ajaxLoader').show();
};

threshold.hideAjaxLoader = function(){
    $('span.ajaxLoader').hide();
};

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
};

threshold.toggleIncludes = function(checkbox){
    if( $(checkbox).prop('checked') ){
        threshold.checkAllInclude();
    } else {
        threshold.unCheckAllInclude();
    }
};

threshold.checkAllInclude = function(){
    var allIncludes = $("#bulkUpdateTable input.includeInBulk") || [];
    for(var i = 0; i < allIncludes.length; i++){
        $(allIncludes[i]).prop('checked', true);
    }
};

threshold.unCheckAllInclude = function(){
    var allIncludes = $("#bulkUpdateTable input.includeInBulk") || [];
    for(var i = 0; i < allIncludes.length; i++){
        $(allIncludes[i]).prop('checked', false);
    }
};

threshold.stripPerCentSymbol = function(str){
    return str.replace(threshold.perCentRepl, '');
};

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
    
};

threshold.setChangedThreshold = function(inp){
    $(inp).parent().removeClass();
    $(inp).parent().addClass('changed');
};

threshold.showSavedThreshold = function(inp){
    var par = $(inp).parent();
    $(par).removeClass('changed');
    $(par).css('background-color', threshold.stdSuccessColor);
    $(par).fadeTo(2000, 0.6);
    $(par).fadeTo(2000, 1.0, function(){
        $(par).css('background-color', threshold.stdBgColor);
        $(par).show();
    });
    return true;
};

threshold.showErrorThreshold = function(inp){
    $(inp).parent().removeClass();
    $(inp).parent().addClass('error');
};

threshold.netboxSearch = function(){
    if(threshold.netboxSearchReq) {
        /* The previous ajax-call is cancelled and replaced with the last */
        threshold.netboxSearchReq.abort();
    }
    threshold.showAjaxLoader();
    threshold.removeMessages();
    var retVal = 0;

    var descr = $('#thresholdDescr').val();
    var sysname = $('#netboxSysname').val();
    // The checkboxes for GW, GSW and SW
    var checkBoxList = $('input:checkbox[name="boxtype"]:checked');
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
    
    var len = checkBoxList.length;
    for(var i = 0; i < len; i++){
        inputData[checkBoxList[i].value] = checkBoxList[i].value;
    }
    threshold.netboxSearchReq = $.ajax({ url: '/threshold/netboxsearch/',
             data: inputData,
             dataType: 'json',
             type: 'POST',
             success: function(data, textStatus, header){
                            if(data.error){
                                threshold.updateMessages(data.message, true);
                                retVal = -1;
                                return retVal;
                            }
                            $('#chosenBoxes').empty();
                            $('#chosenBoxes').append(data.foundboxes);
                            $('#choseninterfaces').empty();
                            $('#choseninterfaces').append(data.foundinterfaces);
                            if(data.types){
                                $('#netBoxModel').empty();
                                $('#netBoxModel').append(data.types);
                            }
                            return retVal;
                     },
             error: function(req, errMsg, errType){
                        return threshold.ajaxError(req, errMsg, errType);
                    },
             complete: function(header, textStatus){
                        threshold.netboxSearchReq = null;
                        return 0;
                       },
             statusCode: {404: function(){
                                return threshold.pageNotFound();
                               },
                          500: function(){
                                return threshold.serverError();
                               }
                        }
        });
    threshold.hideAjaxLoader();
    return retVal;
};


threshold.getBulkUpdateHtml = function(descr, ids){
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
    threshold.getBulkUpdateHtmlReq =
        $.ajax({url: '/threshold/preparebulk/',
                data: inputData,
                dataType: 'text',
                type: 'POST',
                success: function(data, textStatus, header){
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
                error: function(req, errMsg, errType){
                        return threshold.ajaxError(req, errMsg, errType);
                       },
                complete: function(header, textStatus){
                            threshold.getBulkUpdateHtmlReq = null;
                            return 0;
                          },
                statusCode: {404: function(){
                                    return threshold.pageNotFound();
                                },
                             500: function(){
                                    return threshold.serverError();
                                }
                        }
            });

};

threshold.chooseDeviceType = function(the_select, select_val){
    if(threshold.chooseDeviceTypeReq){
        /* The previous ajax-call is cancelled and replaced with the last */
        threshold.chooseDeviceTypeReq.abort();
    }
    threshold.chooseDeviceTypeReq =
        $.ajax({url: '/threshold/choosetype/',
            data: {'descr': select_val},
            dataType: 'json',
            type: 'POST',
            success: function(data, textStatus, header){
                        if(data.error){
                            threshold.updateMessages(data.Message, true);
                            return -1;
                        } 
                        threshold.displayMode = data.message;
                        threshold.netboxSearch();
                        if(threshold.displayMode == 'interface'){
                            $(document).find('#netboxSubmitDiv').hide();
                            $(document).find('#netboxsearch').show();
                            $(document).find('#interfacesearch').show();
                            $(document).find('#interfaceSubmitDiv').show();
                        }
                        if(threshold.displayMode == 'netbox'){
                            $(document).find('#interfaceSubmitDiv').hide();
                            $(document).find('#interfacesearch').hide();
                            $(document).find('#netboxsearch').show();
                            $(document).find('#netboxSubmitDiv').show();
                        }
                        return 0;
                      },
            error: function(req, errMsg, errType){
                        return threshold.ajaxError(req, errMsg, errType);
                    },
            complete: function(header, textStatus){
                        threshold.chooseDeviceTypeReq = null;
                        return 0;
                      },
            statusCode: {404: function(){
                                return threshold.pageNotFound();
                               },
                         500: function(){
                                return threshold.serverError();
                              }
                        }
          });
};

threshold.saveToServer = function(toSave){
    threshold.saveMessage = null;
    threshold.thresholdSaveStatus = 0;
    var objectJSON = $.toJSON(toSave);

    $.ajax({url: '/threshold/thresholdssave/',
            data: {'thresholds': objectJSON},
            dataType: 'json',
            type: 'POST',
            async: false,
            success: function(data, textStatus, header){
                        if(typeof data.error == 'undefined' ){
                            threshold.thresholdSaveStatus = -1;
                            return -1;
                        }
                        if(data.error > 0){
                            threshold.thresholdSaveStatus = -1;
                            threshold.saveMessage = data;
                            return -1;
                        }
                        return 0;
                     },
            error:  function(req, errMsg, errType){
                        threshold.thresholdSaveStatus = -1;
                        return threshold.ajaxError(req, errMsg, errType);
                    },
            complete: function(header, textStatus){
                        return 0;
                      },
            statusCode: {404: function(){
                                threshold.thresholdSaveStatus = -1;
                                return threshold.pageNotFound();
                              },
                         500: function(){
                                threshold.thresholdSaveStatus = -1;
                                return threshold.serverError();
                              }
                        }

            });
    return threshold.thresholdSaveStatus;
};

threshold.findCheckBox = function(name, value){
    var findStr = 'input:checkbox.' + name;
    if(value != null){
        findStr += '[value="' + value +'"]';
    }
    return $(findStr);
};

threshold.saveChosenThresholds = function(allIncludes){
    threshold.removeMessages();
    threshold.showAjaxLoader();
    /* Holds an dict of id, operator and threshold-value */
    var thresholdsToSave = new Array();
    /* An array with ids to update the GUI */
    var chosenIds = new Array();
    for(var i = 0; i < allIncludes.length; i++){
        var chkbox = allIncludes[i];
        var dsId = $(chkbox).val();
        var row = $(chkbox).parents('tr');
        var op = $('select.operator', row).val();
        var thrInput = $('input:text.threshold', row);
        var thrVal = $(thrInput).val();
        var units = $('select.unit', row).val();
        thresholdsToSave[i] = {'dsId' : dsId, 'op': op, 'thrVal': thrVal, 'units': units};
        chosenIds[i] = dsId;
    }
    var saveStatus = 0;
    if(thresholdsToSave.length > 0){
        saveStatus = threshold.saveToServer(thresholdsToSave);
    }
    if(saveStatus == -1){
        var serverMsg = null;
        if(threshold.saveMessage != null){
            /*
             * Something went wrong,- preserve the error-messages from
             * the server
            */
            serverMsg = threshold.saveMessage;
        } else {
            /*
             * Something went wrong,- but we do not know what...
             * Usually a crash on the server.
             * All thresholds are signaled as withdrawn.
            */
            serverMsg = {};
            serverMsg.message = 'Save failed'
            serverMsg.failed = chosenIds.slice();
            serverMsg.error = serverMsg.failed.length;
        }
        threshold.updateMessages(serverMsg.message, true);
        for(var i = 0; i < serverMsg.failed.length; i++){
            var dsId = serverMsg.failed[i];
            var chkbox = threshold.findCheckBox('includeInBulk', dsId);
            var thrInput = $(chkbox).parents('tr').find('input:text.threshold');
            threshold.showErrorThreshold(thrInput);
            /* Remove those who did not get saved */
            var idx = chosenIds.indexOf(dsId);
            if(idx > -1){
                chosenIds.splice(idx, 1);
            }
        }
    }
    for(var i = 0; i < chosenIds.length; i++){
        var chkbox = threshold.findCheckBox('includeInBulk', chosenIds[i]);
        var thrInput = $(chkbox).parents('tr').find('input:text.threshold');
        threshold.showSavedThreshold(thrInput);
    }
    threshold.hideAjaxLoader();
    return 0;
};

threshold.saveSingleThreshold = function(btn){
    threshold.removeMessages();
    var row = $(btn).parents('tr');
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
};


threshold.saveCheckedThresholds = function(){
    var bulkUpdateTable = $('#bulkUpdateTable');
    var bulkUpdateChkBoxes = $('input:checkbox.includeInBulk') || [];
    var allIncludes = Array();
    for(var i = 0; i < bulkUpdateChkBoxes.length; i++){
        if($(bulkUpdateChkBoxes[i]).prop('checked')){
            allIncludes.push(bulkUpdateChkBoxes[i]);
        }
    }
    if(allIncludes.length < 1){
        threshold.updateMessages('Please, check the ones to save', true);
        return -1;
    }
    threshold.saveChosenThresholds(allIncludes);
    return 0;
}; /* saveCheckedThresholds */


threshold.saveAllThresholds = function(){
    threshold.removeMessages();
    var bulkUpdateTable = $('#bulkUpdateTable');
    var allIncludes = $('input:checkbox.includeInBulk', bulkUpdateTable) || [];
    if(allIncludes.length < 1){
        return -1;
    }
    threshold.saveChosenThresholds(allIncludes);
    return 0;
}; /* saveAllThresholds */

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
    var bulkUpdateChkBoxes = $("input.includeInBulk", bulkUpdateTable) || [];
    var allIncludes = Array();
    for(var i = 0; i < bulkUpdateChkBoxes.length; i++){
        if( $(bulkUpdateChkBoxes[i]).prop('checked')){
            allIncludes.push(bulkUpdateChkBoxes[i]);
        }
    }
    if(allIncludes.length < 1){
        threshold.updateMessages('Please, check the ones to update', true);
        return -1;
    }

    $(bulkThrInput).parent().removeClass();
    for(var i = 0; i < allIncludes.length; i++){
        var row = $(allIncludes[i]).parents('tr');

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

    $('#bulkUpdateTable input.toggleIncludes').change(function(){
        threshold.toggleIncludes(this);
    });

    $('#bulkUpdateTable input.threshold').change(function(){
        threshold.setChangedThreshold(this);
    });

    $("#saveCheckedThresholdsTop").click(threshold.saveCheckedThresholds);
    $("#saveAllThresholdsTop").click(threshold.saveAllThresholds);

    $("#saveCheckedThresholdsBottom").click(threshold.saveCheckedThresholds);
    $("#saveAllThresholdsBottom").click(threshold.saveAllThresholds);

}; /* attachBulkListeners */


$(document).ready(function(){
    $('#thresholdDescr').change(function(){
        var sval = $(this).val();
        if(sval == 'empty'){
            return -1;
        }
        threshold.removeMessages();
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
        }, 300);
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
        }, 300);
    });

    $('#netboxSubmit').click(function(){
        threshold.showAjaxLoader();
        threshold.removeMessages();
        var retVal = 0;
        var thresholdDescr = $('#thresholdDescr').val();
        var chosenBoxes = $('#chosenBoxes').val() || [];
        if(chosenBoxes.length > 0){
            threshold.getBulkUpdateHtml(thresholdDescr, threshold.table2String(chosenBoxes));
        } else {
            threshold.updateMessages('No netboxes chosen', true);
            retVal = -1;
        }
        threshold.hideAjaxLoader();
        return retVal;
    });

    $('#interfaceSubmit').click(function(){
        threshold.showAjaxLoader();
        threshold.removeMessages();
        var retVal = 0;
        var descr = $('#thresholdDescr').val();
        var interfaces = $('#choseninterfaces').val() || [];
        if(interfaces.length > 0){
            threshold.getBulkUpdateHtml(descr, threshold.table2String(interfaces));
        } else {
            threshold.updateMessages('No interfaces chosen', true);
            retVal = -1;
        }
        threshold.hideAjaxLoader();
        return retVal;
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
	        var dsid = $(this).parent().attr('data_dsid');
            var rowParent = $(this).parents('tr');
            var thrVal = $('input.thresholdvalue', rowParent).val();
            var operator = $('select.operator', rowParent).val();
            var unit = $('select.unit', rowParent).val();
            threshold.save_threshold(this, dsid, operator, thrVal, unit);
        });
    });

    $('input.thresholdvalue').change(function(){
        threshold.setChangedThreshold(this);
    });
});


threshold.save_threshold = function(updateButton, dsId, op, thrVal, unit){
    threshold.removeMessages();
    if( threshold.save_queue.indexOf(dsId) > -1){
	return -1;
    }
    threshold.save_queue.push(dsId);
    var thrRecord = {'dsId': dsId, 'op': op, 'thrVal': thrVal, 'units': unit};
    var retVal = threshold.saveToServer([thrRecord]);
    if(retVal == -1){
        threshold.callbackFail(updateButton);
        if(threshold.saveMessage != null){
            threshold.updateMessages(threshold.saveMessage.message, true);
        } else {
            threshold.updateMessages('Save failed', true);
        }
    } else {
        threshold.callbackSuccess(updateButton);
    }
    threshold.removeFromQueue(dsId);
    return 0;
};

threshold.callbackSuccess = function(button){
    var maxColumn = $(button).parents("tr").find("td.maxvalue");
    var thrInput = $(button).parents('tr').find('input.thresholdvalue');

    threshold.showSavedThreshold(thrInput);
};

threshold.callbackFail = function(button){
    var thrInput = $(button).parents('tr').find('input.thresholdvalue');
    threshold.showErrorThreshold(thrInput);
};
