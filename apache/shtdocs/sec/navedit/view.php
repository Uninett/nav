<?php

include('formatting.inc.php');
include('access.inc.php');
include('file.inc.php');

list($lock,$user) = locked($file);

if($contents = table_from_file($file)){

print s_header(basename(path_file($file)));

print "<div id=\"content\">";

print "<table><tr>";
if($lock == 1 && $user == user_res()){

  print "<td class=\"menu\"><a title=\"Save changes and return to the menu\" href=\"message.php?file=$file\"><img src=\"home.png\" alt=\"home\"/><br/><b>Home</b></a></td><td class=\"menu\"><a title=\"Advanced mode\" href=\"advanced.php?file=$file\"><img src=\"ikoner/view_text.png\" alt=\"advanced\"/><br/><b>Advanced</b></a></td><td class=\"menu\"><a title=\"Cancel all actions and return to the menu\" href=\"undo.php?file=$file\"><img src=\"ikoner/stop.png\" alt=\"stop\"/><br/><b>Panic</b></a></td>";

} else {

  print "<td class=\"menu\"><a title=\"Return to the menu\" href=\"message.php?file=$file\"><img src=\"home.png\" alt=\"home\"/><br/><b>Home</b></a></td>";

  if(file_is_not_new($file)){
    print "<td class=\"menu\"><a title=\"Unlock this file\" href=\"steal.php?file=$file\"><img src=\"ikoner/unlock.png\" alt=\"unlock\"/><br/><b>Unlock</b></a></td>";
  }
}
 

 print "<td>".get_fileinfo($file)."</td></tr></table>";

  print $contents;


print "</div>";
print s_footer();

} else {

  header("Location: index.php?error=nofile");
  exit;


}
  

?>