<?php

include('access.inc.php');
include('formatting.inc.php');

print s_header("Filliste");

print errormessage($error);

print "<div id=\"menulist\">";
$filliste = list_files();
for($f=0;$f<sizeof($filliste);$f++){
  print get_fileinfo($f,$filliste);
}
print "<div class=\"menurun\"><form action=\"parser.php\" method=\"post\"><input type=\"hidden\" name=\"command\" value=\"run\"><input type=\"image\" alt=\"run\" name=\"run\" src=\"ikoner/exec.png\" class=\"button\" value=\"RUN\"></form><h2>Run the collecting scripts</h2><p>As a background process.</p></div>";

print "</div>";

print s_footer();

?>