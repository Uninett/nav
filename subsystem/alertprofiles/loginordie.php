<?php
function loginOrDie() {
	if (!login) {
		exit(gettext("<p><B>Security error!</B> You have to be logged inn to access this functionality. Contact your system administrator.") );
	}
}
?>
