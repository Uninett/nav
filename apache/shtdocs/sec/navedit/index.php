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
print "</table></div>";

print s_footer();

?>