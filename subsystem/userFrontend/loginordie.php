<?php
function loginOrDie() {
	if (!login) {
		exit("<p><B>Alvorlig feil!</B> Du må være innlogget for å nå denne funksjonaliteten. Kontakt Systemadministrator.");
	}
}
?>
