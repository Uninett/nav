<?php 

include('formatting.inc.php');
include('access.inc.php');
include('file.inc.php');

if(is_array($felt)){
  $data = join("",$felt);
} else {
  $data = $felt;
}

if ($cancel||$cancel_x){

  header("Location:view.php?file=$file");

} elseif($option!="blank"&&!$ok) {

  list($table_start,$table_end) = table_start_end($file,$row,"new");

  if($option == "copyprevious"){

    $previous = nav_make_row_from_file($file,$row-1);

    if(is_array($previous)){
      $type = "row";
    } else {
      $type = "comment";
    }

  }
  $restmeny = "<td><input type=\"image\" name=\"option\" value=\"blank\" src=\"ikoner/key_enter.png\" alt=\"empty\" id=\"radio\"/></td><td>empty line</td><td><input type=\"image\" name=\"option\" value=\"copyprevious\" src=\"ikoner/editcopy.png\" alt=\"copy\" id=\"radio\"/></td><td>copy previous line</td>";

  if($type=="comment"){
    $radiomeny = "<table><tr><td><input type=\"image\" name=\"type\" value=\"row\" src=\"ikoner/radio_no.png\" alt=\"empty\" id=\"radio\"/></td><td>data</td><td><img src=\"ikoner/radio_yes.png\" alt=\"filled\"/></td><td>kommentar</td>".$restmeny."</tr></table>";

    if($option == "copyprevious"){
      $felt = $previous;
    } else {
      $felt = join(":",$felt);
    }

    $radfelt = "<td class=\"galskap\" colspan=\"$col\"><input type=\"text\" name=\"felt\" value=\"".uncomment($felt)."\" size=\"85\"/></td>";
  } else {
    //type = row
    $radiomeny = "<table><tr><td><img src=\"ikoner/radio_yes.png\" alt=\"filled\"/></td><td>data</td><td><input type=\"image\" name=\"type\" value=\"comment\" src=\"ikoner/radio_no.png\" alt=\"comment\" id=\"radio\"/></td><td>comment</td>".$restmeny."</tr></table>";

    $std_size = floor(85/$col);

    if($option == "copyprevious"){
      $felt = $previous;
    } else {
      $felt = nav_file_split(uncomment($felt));
    }

    for ($i = 0; $i < $col; $i++) {
      if(!$size = strlen($felt[$i])){
	$size=$std_size;
      }
      $radfelt .= "\n\t\t<td class=\"galskap\"><input type=\"text\" name=\"felt[]\" value=\"".$felt[$i]."\" size=\"$size\"/></td>";
    }

  }


  $settinnikon = "<input type=\"image\" name=\"cancel\" alt=\"cancel\" title=\"Cancel Insert\" value=\"1\" src=\"ikoner/button_cancel.png\" class=\"button\"/><input type=\"image\" name=\"ok\" alt=\"ok\" title=\"Lagre endringer\" value=\"1\" src=\"ikoner/button_ok.png\" class=\"button\"/>";

  $radio = "<form action=\"$PHP_SELF\"><input type=\"hidden\" name=\"operation\" value=\"insert\"/><input type=\"hidden\" name=\"file\" value=\"$file\"/><input type=\"hidden\" name=\"row\" value=\"$row\"/><input type=\"hidden\" name=\"col\" value=\"$col\"/><table><tr><td><input type=\"hidden\" name=\"type\" value=\"$type\"/>$radiomeny</td></tr><tr><td>\n<table>".$table_start."<tr>".$radfelt."</tr>".$table_end."</table>\n</td></tr><tr><td id=\"formsubmit\">$settinnikon</td></tr></table></form>";

  print s_header("Test");

  print "<div id=\"content\"><h1>Insert</h1>$radio</div>";

  print s_footer();

} else {

  //print $QUERY_STRING;
  header("Location:parser.php?$QUERY_STRING");
  exit;

}