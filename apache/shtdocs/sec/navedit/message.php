<?php

include('formatting.inc.php');
include('access.inc.php');
include('file.inc.php');

list($lock,$user) = locked($file);

if(isset($file) && $lock == 1 && $user == user_res()){

  if($cancel){

    header("Location: view.php?file=$file");

  } elseif($ok && $commit){
    header("Location: unlock.php?file=$file&commit=$commit");

  } else {
    
    if($ok){
      $warning = "<p class=\"warning\">Du MÅ skrive noe her</p>";
    }

    $log = shell_exec("rcsdiff ".path_file($file));

    if($log){
      $settinnikon = "<span title=\"Avbryt og gå tilbake til fila\"><input type=\"image\" name=\"cancel\" alt=\"cancel\" value=\"1\" src=\"ikoner/button_cancel.png\" class=\"button\"/></span><span title=\"Lagre endringer\"><input type=\"image\" name=\"ok\" alt=\"ok\" value=\"1\" src=\"ikoner/button_ok.png\" class=\"button\"/></span>";
      $help = "<p>Fila er endret. Du kan lese i endringsloggen lenger ned på siden hva som faktisk er endret. </p><p>Kommenter endringene dine her (til bruk for logging til RCS).</p>$warning<p><form action=\"$PHP_SELF\" method=\"POST\"><input type=\"hidden\" name=\"file\" value=\"$file\"/><table><tr><td><textarea name=\"commit\" rows=\"5\" cols=\"82\">$commit</textarea></td></tr><tr><td id=\"formsubmit\">$settinnikon</td></tr></table></form>";
	
      //endringer har skjedd

      print s_header("Test");
    
      print "<div id=\"content\"><h1>Lagre endringer</h1>$help";
    
      print "<h2>Endringslogg</h2><pre>".$log."</pre></div>";

      print s_footer();

    } else {
      //ingen endringer
      header("Location:unlock.php?file=$file");
      exit;
    }

  } 
} else {

  header("Location:index.php");
}

?>
