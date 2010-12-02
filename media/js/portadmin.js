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
var queue = new Array();

$(document).ready(function(){
	add_change_listener_to_fields();
});

function add_change_listener_to_fields() {
	$(".ifalias, .vlanlist").change(function(){
		var row = $(this).parents("tr");
		$(row).addClass("changed");
		$(row).find("td").addClass("changed");
		$(row).find("img.save").removeClass("hidden");
	});
}

function save_row(rowid) {
	/*
	 * This funcion does an ajax call to save the information given by the user
	 * when the save-button is clicked.
	 */

	// If a save on this row is already in progress, do nothing.
	if (queue.indexOf(rowid) > -1) {
		return;
	}
	disable_saveall_buttons();
	
	queue.push(rowid)
	
	var row = $("#" + rowid);
	var ifalias = $(row).find(".ifalias").val();
	var vlan = $(row).find(".vlanlist").val();
	
	// Post data and wait for json-formatted returndata. Display status information to user
	$.ajax({url: "save_interfaceinfo", 
			data: {'ifalias': ifalias, 'vlan': vlan, 'interfaceid': rowid}, 
			dataType: 'json',
			type: 'POST',
			success: function(data){
					display_callback_info(row, data);
					clear_changed_state(row);
				},
			error: function(request, errorMessage, errortype){
					var data = {};
					data.error = 1;
					data.message = errorMessage + " - Hm, perhaps try to log in again?";
					display_callback_info(row, data);
				},
			complete: function(){
					remove_from_queue(rowid);
					if (queue.length == 0) {
						enable_saveall_buttons();
					}
				}
	});
}

function bulk_save() {
	$("tr.changed").each(function(){
		var id = $(this).attr("id");
		save_row(id);
	});
}

function remove_from_queue(id) {
	var index = queue.indexOf(id);
	if (index > -1) {
		queue.splice(index, 1);
	}
}

function disable_saveall_buttons() {
	$("input.saveall_button").attr('disabled', 'disabled');
}

function enable_saveall_buttons() {
	$("input.saveall_button").removeAttr('disabled');
}


function clear_changed_state(row) {
	$(row).removeClass("changed");
	$(row).find("td").removeClass("changed");
	$(row).find("img.save").addClass("hidden");
}

function display_callback_info(row, data) {
	// Create new element
	var div = $("<div></div>").addClass("saveinfo");
	$("<p />").appendTo(div);
	$("body").append(div);

	// Add click-listener to remove element
	$(div).click(function(){
		$(this).remove();
	});
	
	// Calculate and set position
	var pos = $(row).find("td:last").offset(); // pos of last cell in row
	var left = pos.left + 30;
	var top = pos.top - 1;
	$(div).css({ "left": left + "px", "top": top + "px" });

	// Add correct layout
	if (data.error) {
		$(div).addClass("error");
	} else {
		$(div).addClass("success");
	}

	// Set message and show element
	$(div).find("p").html(data.message);
	$(div).show();

	// Automatically remove success messages
	if (!data.error) {
		$(div).fadeOut(6000, function(){
			$(this).remove();
		});
	}
}
