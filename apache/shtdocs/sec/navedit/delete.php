<?php 

include('access.inc.php');
include('file.inc.php');
include('formatting.inc.php');


if ($cancel||$cancel_x){

   header("Location:view.php?file=$file");

} elseif($col) {

  $rad = nav_make_row_from_file($file,$row,$col);

  $table = "<p><table>";
  if(is_array($rad)){
    $table .= "\n\t<tr>";
    for($r = 0; $r < $col; $r++){
      $table .= "\n\t\t<td class=\"galskap\">".$rad[$r]."</td>";
    }
    $table .= "\n\t</tr>";
  } else {
    $table .= "\n\t<tr><td colspan=\"$cols\" class=\"galskap\">".uncomment($rad)."</td></tr>";
  }
  $table .= "</table></p>";

  $tekst = "<p>Er du helt sikker på at du vil slette rad $row?</p>$table$buttons";
  $settinnikon = "<span title=\"Nei\"><input type=\"image\" name=\"cancel\" alt=\"cancel\" value=\"1\" src=\"ikoner/button_cancel.png\" class=\"button\"/></span><span title=\"Ja\"><input type=\"image\" name=\"ok\" alt=\"ok\" value=\"1\" src=\"ikoner/button_ok.png\" class=\"button\"/></span>";
  $innhold = "<p><form action=\"$PHP_SELF\"><input type=\"hidden\" name=\"operation\" value=\"delete\"><input type=\"hidden\" name=\"file\" value=\"$file\"><input type=\"hidden\" name=\"row\" value=\"$row\"><table><tr><td>$tekst</td></tr><tr><td id=\"formsubmit\">$settinnikon</td></tr></table></form></p>";

print s_header("Test");

print "<div id=\"content\"><h1>Slett rad</h1>$innhold</div>";

print s_footer();
} else {

  header("Location:parser.php?$QUERY_STRING");

}

}