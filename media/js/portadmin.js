function save_row(rowid) {
	/*
	 * This funcion does an ajax call to save the information given by the user
	 * when the save-button is clicked.
	 */
	
	// Fetch values from the fields
	var row = $("#" + rowid);
	var ifalias = $(row).find(".ifalias").val();
	var vlan = $(row).find(".vlanlist").val();
	
	// Post data and wait for json-formatted returndata. Display status information to user
	$.post("save_interfaceinfo", 
			{'ifalias': ifalias, 'vlan': vlan, 'interfaceid': rowid}, 
			function(data){
				var div = $("div#saveinfo");
				var pos = $(row).find("td:last").offset(); // pos of last cell in row
				var left = pos.left + 60;
				var top = pos.top - 15;
				
				if (data.error) {
					$(div).attr("class", "error");
				} else {
					$(div).attr("class", "success");
				}
				$(div).find("p").html(data.message);
				$(div).css({ "left": left + "px", "top": top + "px" });
				$(div).show();
			}, 'json');
}