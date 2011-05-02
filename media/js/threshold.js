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

var typeDelay = function(){
    var timer = 0;
    return function(callback, ms){
        clearTimeout (timer);
        timer = setTimeout(callback, ms);
    }  
}();

var threshold = threshold || {};

threshold.netboxSearchReq = null;
threshold.displayMode = '';
threshold.stdBgColor = 'white';
threshold.stdErrColor = 'red';
threshold.stdSuccessColor = 'green';
threshold.perCentRepl = new RegExp('%*$');
threshold.descriptionRegExp = new RegExp('^[a-zA-Z][a-zA-Z0-9\ ]+$');
threshold.thresholdSaveStatus = 0;
threshold.save_queue =  new Array();

threshold.removeFromQueue = function(id){
    var idx = threshold.save_queue.indexOf(id);
    if(idx > -1){
	threshold.save_queue.splice(idx, 1);
    }
};

threshold.backToSearch = function(){
    $('div.#netboxsearch').show();
    if(threshold.displayMode == 'interface'){
        $('div.#interfacesearch').show();
    }
    var bulkUpdateData = $('div.#bulkupdateDiv');
    $(bulkUpdateData).hide();
    $(bulkUpdateData).empty();
    threshold.removeMessages();
};

threshold.removeMessages = function(){
    var messagesDiv = $('div.#messagesDiv');
    $(messagesDiv).empty();
};

threshold.updateMessages = function(msg, isError){
    var messagesDiv = $('div.#messagesDiv');
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

threshold.ajaxError = function( request, ErrMessage, errType){
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

threshold.toggleIncludes = function(){
    var checkBox = $('input:checkbox[name="toggleIncludes"]');
    if($(checkBox).attr('checked')){
        threshold.checkAllInclude();
    } else {
        threshold.unCheckAllInclude();
    }
};

threshold.checkAllInclude = function(){
    var allIncludes = $('input:checkbox[name="include"]') || [];
    for(var i = 0; i < allIncludes.length; i++){
        allIncludes[i].checked = true;
    }
};

threshold.unCheckAllInclude = function(){
    var allIncludes = $('input:checkbox[name="include"]:checked') || [];
    for(var i = 0; i < allIncludes.length; i++){
        allIncludes[i].checked=false;
    }
};

threshold.stripPerCentSymbol = function(str){
    return str.replace(threshold.perCentRepl, '');
};

/*
    NB!
    Always remember to keep error-chekcing here and on server in sync!
*/
threshold.isLegalThreshold = function(thr){
    var intValue = parseInt(threshold.stripPerCentSymbol(thr));
    return (intValue > -1);
    
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
        threshold.netboxSearchReq.abort();
    }
    threshold.showAjaxLoader();
    threshold.removeMessages();
    var retVal = 0;

    var descr = $('select.#descr').val();
    var sysname = $('input.#netboxname').val();
    // The checkboxes for GW, GSW and SW
    var checkBoxList = $('input:checkbox[name="boxtype"]:checked');
    var vendor = $('select.#vendor').val();
    var model = $('select.#model').val();
    var ifname = $('input.#interfacename').val();
    var upDown = $('input:checkbox[name="updown"]:checked').val();

    var boxes = $('select.#chosenboxes').val() || [];
    
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
                            $('select.#chosenboxes').empty();
                            $('select.#chosenboxes').append(data.foundboxes);
                            $('select.#choseninterfaces').empty();
                            $('select.#choseninterfaces').append(data.foundinterfaces);
                            if(data.types){
                                $('select.#model').empty();
                                $('select.#model').append(data.types);
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
                               }
                        }
        });
    threshold.hideAjaxLoader();
    return retVal;
};


threshold.getBulkUpdateHtml = function(descr, ids){
    if(! threshold.isLegalDescription(descr)){
        threshold.updateMessages('Illegal threshold description', true);
        return -1;
    }
    var inputData = {
        'descr': descr,
        'ids': ids
        };
    $.ajax({url: '/threshold/preparebulk/',
                data: inputData,
                dataType: 'text',
                type: 'POST',
                success: function(data, textStatus, header){
                            if(data.error){
                                threshold.updateMessages(data.message, true);
                                return -1;
                            }
                            $('div.#netboxsearch').hide();
                            $('div.#interfacesearch').hide();
                            $('div.#bulkupdateDiv').show();
                            $('div.#bulkupdateDiv').html(data);
                        },
                error: function(req, errMsg, errType){
                        return threshold.ajaxError(req, errMsg, errType);
                       },
                complete: function(header, textStatus){
                            return 0;
                          },
                statusCode: {404: function(){
                                    return threshold.pageNotFound();
                                }
                        }
            });

};

threshold.chooseDeviceType = function(the_select, select_val){
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
                            $(document).find('div.#netboxSubmitDiv').hide();
                            $(document).find('div.#netboxsearch').show();
                            $(document).find('div.#interfacesearch').show();
                            $(document).find('div.#interfaceSubmitDiv').show();
                        }
                        if(threshold.displayMode == 'netbox'){
                            $(document).find('div.#interfaceSubmitDiv').hide();
                            $(document).find('div.#interfacesearch').hide();
                            $(document).find('div.#netboxsearch').show();
                            $(document).find('div.#netboxSubmitDiv').show();
                        }
                        return 0;
                      },
            error: function(req, errMsg, errType){
                        return threshold.ajaxError(req, errMsg, errType);
                    },
            complete: function(header, textStatus){
                          return 0;
                       },
            statusCode: {404: function(){
                                return threshold.pageNotFound();
                               }
                        }
          });
};

threshold.saveThresholds = function(dsIds, operator, thrValue){
    threshold.thresholdSaveStatus = 0;
    $.ajax({url: '/threshold/savethresholds/',
            data: { 'dsIds': dsIds,
                    'operator': operator,
                    'threshold': thrValue
                  },
            dataType: 'json',
            type: 'POST',
            async: false,
            success: function(data, textStatus, header){
                        if(data.error){
                            threshold.updateMessages(data.message, true);
                            threshold.thresholdSaveStatus = -1;
                            return -1;
                        }
                        return 0;
                    },
            error: function(req, errMsg, errType){
                    return threshold.ajaxError(req, errMsg, errType);
                   },
            complete: function(header, textStatus){
                        return 0;
                      },
            statusCode: {404: function(){
                                return threshold.pageNotFound();
                               }
                        }
            });
    return threshold.thresholdSaveStatus;
};


threshold.bulkSaveThresholds = function(){
    threshold.removeMessages();
    var allIncludes = $('input:checkbox[name="include"]:checked') || [];
    var bulkOperator = $('select.#bulkOperator').val();
    var bulkThreshold = $('input.#bulkThreshold').val();
    if(allIncludes.length == 0){
        errMsg = 'No thresholds are chosen. Please, check the ones to update';
        threshold.updateMessages(errMsg, true);
        return -1;
    }
    
    threshold.showAjaxLoader();
    var dsIds = new Array(allIncludes.length);
    for(var i = 0; i < allIncludes.length; i++){
        dsIds[i] = allIncludes[i].value;
    }
    var ret = threshold.saveThresholds(threshold.table2String(dsIds),
                                        bulkOperator, bulkThreshold);
    if(ret == -1 ){
        threshold.updateMessages('Save failed', true);
        return -1;
    }
    threshold.hideAjaxLoader();
    return 0;
    
};

threshold.saveSingleThreshold = function(btn){
    threshold.removeMessages();
    var row = $(btn).parents('tr');
    var dsId = $(row).find('input:checkbox[name="include"]').val();
    var op = $(row).find('select').val();
    var thrInput = $(row).find('input.#threshold');
    var thr = $(thrInput).val();

    if(! threshold.isLegalThreshold(thr)){
        threshold.updateMessages('Save failed. Illegal threshold', true);
        threshold.showErrorThreshold(thrInput);
        return -1;
    }       
    
    var ret = threshold.saveThresholds(dsId, op, thr);
    if(ret == -1){
        threshold.updateMessages('Save failed', true);
        threshold.showErrorThreshold(thrInput);
        return -1;
    } else {
        threshold.showSavedThreshold(thrInput);
    }
    threshold.updateMessages('Threshold saved', false);
    return 0;
};

threshold.saveCheckedThresholds = function(){
    threshold.removeMessages();
    var allIncludes = $('input:checkbox[name="include"]:checked') || [];
    if(allIncludes.length < 1){
        threshold.updateMessages('Please, check the ones to save', true);
        return -1;
    }
    threshold.showAjaxLoader();
    var numbErrors = 0;
    for(var i = 0; i < allIncludes.length; i++){
        var chkbox = allIncludes[i];

        var dsId = $(chkbox).val();
        var row = $(chkbox).parents('tr');
        var op = $(row).find('select').val();

        var thrInput = $(row).find('input.#threshold');
        var thr = $(thrInput).val();
        if(! threshold.isLegalThreshold(thr)){
            threshold.showErrorThreshold(thrInput);
            numbErrors++;
        } else {
            var ret = threshold.saveThresholds(dsId, op, thr);
            if(ret == -1){
                threshold.showErrorThreshold(thrInput);
                numbErrors++;
            } else {
                threshold.showSavedThreshold(thrInput);
            }
        }
    }
    if(numbErrors > 0){
        var errMsg = numbErrors + ' error' + (numbErrors > 1 ? 's' : '');
        errMsg += '. Check for illegal values';
        threshold.updateMessages(errMsg, true);
    } else {
        threshold.updateMessages('All checked thresholds saved', false);
    }
    threshold.hideAjaxLoader();
    return 0;
};

threshold.saveAllThresholds = function(){
    threshold.removeMessages();
    var allIncludes = $('input:checkbox[name="include"]') || [];
    if(allIncludes.length < 1){
        return -1;
    }
    threshold.showAjaxLoader();
    var numbErrors = 0;
    for(var i = 0; i < allIncludes.length; i++){
        var chkbox = allIncludes[i];

        var dsId = $(chkbox).val();
        var row = $(chkbox).parents('tr');
        var op = $(row).find('select').val();

        var thrInput = $(row).find('input.#threshold');
        var thr = $(thrInput).val();
        if(! threshold.isLegalThreshold(thr)){
            threshold.showErrorThreshold(thrInput);
            numbErrors++;
        } else {
            var ret = threshold.saveThresholds(dsId, op, thr);
            if(ret == -1){
                threshold.showErrorThreshold(thrInput);
                numbErrors++;
            } else {
                threshold.showSavedThreshold(thrInput);
            }
        }
    }
    if(numbErrors > 0){
        var errMsg = numbErrors + ' error' + (numbErrors > 1 ? 's': '');
        errMsg += '.  Check for illegal values';
        threshold.updateMessages(errMsg, true);
    } else {
        threshold.updateMessages('All thresholds saved', false);
    }
    threshold.hideAjaxLoader();
    return 0;
};

threshold.bulkUpdateThresholds = function(btn){
    threshold.removeMessages();
    var allIncludes = $('input:checkbox[name="include"]:checked') || [];

    var bulkRow = $(btn).parents('tr');
    var bulkOperator = $(bulkRow).find('select').val();
    var bulkThrInput= $(bulkRow).find('input.#bulkThreshold');
    var bulkThr = $(bulkThrInput).val();

    if(! threshold.isLegalThreshold(bulkThr)){
        threshold.updateMessages('Illegal threshold', true);
        threshold.showErrorThreshold(bulkThrInput);
        return -1;
    }

    if(allIncludes.length < 1){
        threshold.updateMessages('Please, check the ones to update', true);
        return -1;
    }

    $(bulkThrInput).parent().removeClass();
    for(var i = 0; i < allIncludes.length; i++){
        var dsId = allIncludes[i].value;
        var chkbox = $('input:checkbox[value="'+dsId+'"]:checked');
        var row = $(chkbox).parents('tr');

        $(row).find('select').val(bulkOperator);

        var thrInput = $(row).find('input.#threshold');
        $(thrInput).val(bulkThr);
        // Mark as changed
        threshold.setChangedThreshold(thrInput);
        
    }
};

$(document).ready(function(){
    $('select.#descr').change(function(){
        var sval = $(this).val();
        if(sval == 'empty'){
            return -1;
        }
        threshold.removeMessages();
        if(! threshold.isLegalDescription(sval)){
            threshold.updateMessages('Illegal threshold description', true);
            return -1;
        }
        $('div.#bulkupdateDiv').hide();
        threshold.chooseDeviceType(this, sval);
    });

    $('input.#netboxname').keyup(function(){
        typeDelay(function(){
            threshold.netboxSearch();
        }, 300);
    });

    $('input:checkbox').change(function(){
        threshold.netboxSearch();
    });

    $('select.#vendor').change(function(){
        threshold.netboxSearch();
    });
        
    $('select.#model').change(function(){
        threshold.netboxSearch();
    });

    $('select.#chosenboxes').change(function(){
        if(threshold.displayMode == 'interface'){
            threshold.netboxSearch();
        }
    });
    
    $('input.#interfacename').keyup(function(){
        typeDelay(function(){
            threshold.netboxSearch();
        }, 300);
    });

    $('input.#netboxsubmit').click(function(){
        threshold.showAjaxLoader();
        threshold.removeMessages();
        var retVal = 0;
        var descr = $('select.#descr').val();
        var boxes = $('select.#chosenboxes').val() || [];
        if(boxes.length > 0){
            threshold.getBulkUpdateHtml(descr, threshold.table2String(boxes));
        } else {
            threshold.updateMessages('No netboxes chosen', true);
            retVal = -1;
        }
        threshold.hideAjaxLoader();
        return retVal;
    });

    $('input.#interfacesubmit').click(function(){
        threshold.showAjaxLoader();
        threshold.removeMessages();
        var retVal = 0;
        var descr = $('select.#descr').val();
        var interfaces = $('select.#choseninterfaces').val() || [];
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
        $(this).parent().find('img.#plus').toggle();
        $(this).parent().find('img.#minus').toggle();
	$(this).parent().parent().find('table.vertitable').toggle();
    });

    $('div.netboxcontainer').find('input.button').each(function(){
        $(this).click(function(){
	    var dsid = $(this).parent().attr('data_dsid');
	    var thrVal = $(this).parents('tr').find('input.thresholdvalue').val();
            var operator = $(this).parents('tr').find('select').val();
            threshold.save_threshold(this, dsid, operator, thrVal);
        });
		
    });

    $('input.thresholdvalue').change(function(){
        threshold.setChangedThreshold(this);
    });
});


threshold.save_threshold = function(updateButton, dsid, operator, thrVal){
    if( threshold.save_queue.indexOf(dsid) > -1){
	return;
    }
    threshold.save_queue.push(dsid);
    $.ajax( { url: '/threshold/savethresholds/',
	      data: { 'dsIds': dsid,
                      'operator': operator,
                      'threshold': thrVal
                    },
	      dataType: 'json',
	      type: 'POST',
	      success: function(data){
                        var retval = 0;
		        if(data.error){
                            threshold.callbackFail(updateButton);
                            threshold.updateMessages(data.message, true);
                            retVal = -1;
			 } else {
			    threshold.callbackSuccess(updateButton);
                         }
		         threshold.removeFromQueue(dsid);
                         return retVal;
		       },
	      error: function(req, errMsg, errType){
                        return threshold.ajaxError(req, errMsg, errType);
                     },
	      complete: function(){
		            threshold.removeFromQueue(dsid);
                            return 0;
		        },
            statusCode: {404: function(){
                                return threshold.pageNotFound();
                              }
                        }
            });
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
