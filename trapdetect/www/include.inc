<?php

function tittel($title) {
	echo "<html>\n";
	echo "<head>\n";
	echo "<title>$title</title>\n";
	echo "</head>\n";
	echo "<body bgcolor=\"#DED2CB\" text=\"#000000\" alink=\"blue\" vlink=\"red\">\n";

	echo "<table width=\"100%\">\n";
	echo "<tr><td width=\"20%\">\n";

		echo "<table width=\"100%\">\n";
		echo "<tr><td>\n";
		echo "<img src=\"gif/trapdetect.gif\" width=\"200\">\n";
		echo "</td></tr>";
		echo "</table>";

	echo "</td><td width=\"80%\">\n";

		echo "<table width=\"100%\">";
		echo "<tr><td>\n";
		echo "<center><a href=\"http://www.nav.ntnu.no\"><img src=\"nett_heading.jpg\" border=\"0\"></a><br><br><br>\n";
		echo "</center>\n";
}

function tittelspesial($title) {
	echo "<html>\n";
	echo "<head>\n";
	echo "<meta http-equiv=\"refresh\" content=\"2\" url=admin.php\">\n";
	echo "<title>$title</title>\n";
	echo "</head>\n";
	echo "<body bgcolor=\"#DED2CB\" text=\"#000000\" alink=\"blue\" vlink=\"red\">\n";

	echo "<table width=\"100%\">\n";
	echo "<tr><td width=\"20%\">\n";

		echo "<table width=\"100%\">\n";
		echo "<tr><td>\n";
		echo "<img src=\"gif/trapdetect.gif\" width=\"200\">\n";
		echo "</td></tr>";
		echo "</table>";

	echo "</td><td width=\"80%\">\n";

		echo "<table width=\"100%\">";
		echo "<tr><td>\n";
		echo "<center><a href=\"http://www.nav.ntnu.no\"><img src=\"nett_heading.jpg\" border=\"0\"></a><br><br><br>\n";
		echo "</center>\n";
}

function topptabell($where) {
		echo "<br>\n";
		echo "</td></tr>\n";
		echo "</table>\n";
	echo "</td></tr>\n";
	echo "<tr><td width=\"20%\" valign=\"top\">\n";

		echo "<table width=\"100%\" bgcolor=\"#ffffff\" cellpadding=\"5\">\n";
		echo "<tr><td>\n";
		echo "<br><b><u>STATUS</u></b><br>\n";
		echo "<a href=\"index.php\">Status nå</a><br>\n";

		echo "<br><b><u>HENDELSESREGISTER</u></b><br>\n";
		echo "<a href=\"history.php?dato=".date("dmy")."\">Dagens (24.00 ->)</a><br>\n";
		echo "<form action=history.php method=GET>\n";
		$day = date("dmy", mktime(0,0,0,date("m"),date("d")-1,date("Y")));
		echo "Tidligere register: <input type=text name=dato size=6 maxlength=6 value=$day>\n";
		echo "</form>\n";

		echo "<br><b><u>LOGG</u></b><br>\n";
		$file_size = filesize("/home/trapdet/log/traplog");
		if ($file_size >= 1073741824) { 
			$file_size = round($file_size / 1073741824 * 100) / 100 . "g"; 
		} elseif ($file_size >= 1048576) { 
			$file_size = round($file_size / 1048576 * 100) / 100 . "m"; 
		} elseif ($file_size >= 1024) { 
			$file_size = round($file_size / 1024 * 100) / 100 . "k"; 
		} else { 
			$file_size = $file_size . "b"; 
		} 

		echo "<a href=\"traplog.php\">Dagens (24.00 ->)</a>&nbsp;$file_size<br>\n";
		echo "<form action=traplogbak.php method=GET>\n";
		$day = date("dmy", mktime(0,0,0,date("m"),date("d")-1,date("Y")));
		echo "Tidligere logg: <input type=text name=dato size=6 maxlength=6 value=$day$rest>\n";
		echo "</form>\n";

		echo "<br><b><u>STATISTIKK</u></b><br>\n";
		echo "<a href=\"statistikk.php\">Generelt</a><br>\n";
		echo "<a href=\"statistikk_ant.php\">Traps pr. enhet</a><br>\n";
		echo "<a href=\"statistikk_oid.php\">Traps inn</a><br>\n";

		echo "<br><b><u>DIVERSE</u></b><br>\n";
		echo "<a href=\"admin.php\">Redigering av innlegg</a><br>\n";
		echo "<br><a href=\"hjelp.php\">HJELP</a><br>\n";
		echo "<p align=center><a href=\"http://www.php.net\"><img src=\"gif/php.gif\" border=0></a></p>";

		echo "</td></tr>\n";
		echo "</table>\n";

	echo "</td><td width=\"80%\" valign=\"top\">\n";

		echo "<table width=\"100%\">\n";
		echo "<tr><td>\n";
		echo "<a name=\"topp\"></a>\n";
		echo "<a href=\"#bunn\">Ned</a>\n";
		echo "</td><td align=right>";
		echo "<a href=\"hjelp.php#$where\">Hjelp</a>";
		echo "</td></tr><tr><td colspan=2>";
		echo "<hr>\n";
		echo "<p>\n";
}

function bunntabell() {

		echo "</p>\n";
		echo "<a name=\"bunn\"></a>\n";
		echo "<hr>\n";
		echo "<a href=\"#topp\">Opp</a>";
		echo "</td></tr>\n";
		echo "</table>\n";

	echo "</td></tr>\n";
	echo "</table>\n";
	echo "<p><center>John Magne Bredal &copy; ".date("Y")."</center>\n";
	echo "</body></html>\n";
}

?>