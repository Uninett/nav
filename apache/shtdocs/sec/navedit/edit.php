<?php 

include('access.inc.php');
include('file.inc.php');
include('formatting.inc.php');

if(is_array($felt)){
  $data = join("",$felt);
} else {
  $data = $felt;
}
if ($cancel){

  header("Location:view.php?file=$file");
  exit;

} elseif(!$data) {

  list($table_start,$table_end) = table_start_end($file,$row,"edit");
 

  $rad = nav_make_row_from_file($file,$row,$col);
  $benevning = "rad";

  if(is_array($rad)){
  $std_size = floor(85/sizeof($rad));

    foreach($rad as $k => $r){
      if(!$size = strlen($r)){
	$size=$std_size;
      }
      $radfelt .= "\n\t\t<td><input type=\"text\" name=\"felt[]\" value=\"$r\" size=\"$size\"/></td>";
    }
  } else {
    $radfelt = "\n\t\t<td colspan=\"".$col."\"><input type=\"text\" name=\"felt\" value=\"".uncomment($rad)."\" size=\"85\"/></td>";
    $benevning = "kommentar";
  }

$settinnikon = "<input type=\"image\" name=\"cancel\" alt=\"cancel\" value=\"1\" src=\"ikoner/button_cancel.png\" title=\"Cancel update\" class=\"button\"/>
<input type=\"image\" name=\"ok\" alt=\"ok\" value=\"1\" src=\"ikoner/button_ok.png\" title=\"Lagre endringer\" class=\"button\"/>";

$rad = "<form action=\"$PHP_SELF\"><input type=\"hidden\" name=\"operation\" value=\"update\"><input type=\"hidden\" name=\"file\" value=\"$file\"><input type=\"hidden\" name=\"row\" value=\"$row\"><input type=\"hidden\" name=\"col\" value=\"$col\"><table><tr><td><table>".$table_start."<tr>$radfelt</tr>".$table_end."</table></td></tr><tr><td id=\"formsubmit\">$settinnikon</td></tr></table></form>";

print s_header("Test");

print "<div id=\"content\"><h1>Endring av $benevning</h1>$rad</div>";

print s_footer();
} else {

  header("Location:parser.php?$QUERY_STRING");
  exit;

}