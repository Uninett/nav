<?php 

include('access.inc.php');
include('file.inc.php');
include('formatting.inc.php');


if($ok){
  
  header("Location:release.php?file=$file");
  exit;
  
} elseif ($cancel||$cancel_x){
  
  header("Location:view.php?file=$file");
  exit;
  
} else {
  
  $tekst = "<p>".path_file($file)."</p><p>Are you really sure you want undo all the changes on this file?</p>$buttons";
  $settinnikon = "<span title=\"Nei\"><input type=\"image\" name=\"cancel\" alt=\"cancel\" value=\"1\" src=\"ikoner/button_cancel.png\" class=\"button\"/></span><span title=\"Ja\"><input type=\"image\" name=\"ok\" alt=\"ok\" value=\"1\" src=\"ikoner/button_ok.png\" class=\"button\"/></span>";
  $innhold = "<p><form action=\"$PHP_SELF\"><input type=\"hidden\" name=\"operation\" value=\"delete\"><input type=\"hidden\" name=\"file\" value=\"$file\"><input type=\"hidden\" name=\"row\" value=\"$row\"><table><tr><td>$tekst</td></tr><tr><td id=\"formsubmit\">$settinnikon</td></tr></table></form></p>";

print s_header("Test");

print "<div id=\"content\"><h1>Undo</h1>$innhold</div>";

print s_footer();

}