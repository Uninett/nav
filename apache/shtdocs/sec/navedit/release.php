<?php

include('formatting.inc.php');
include('access.inc.php');
include('file.inc.php');

list($lock,$user) = locked($file);

if(isset($file) && $lock == 1 && ($user == user_res() || file_is_not_new($file))){
  
  unlock_nrs($file);

  if(!$commit){

    copy(path_nrt($file),path_file($file));

    // ikke som jeg vil kopierer tilbake gammel versjon i stedet; 
    //exec("/usr/bin/rcs -u 2>&1 ".path_file($file));
  }
  
  exec("/usr/bin/ci -u -m'".user_res().":\t$commit' ".path_file($file));

  unlink(path_nrt($file));

  header("Location: index.php");
  exit;

} else {
  
  header("Location: ".$_SERVER['HTTP_REFERER']."&error=notmyfile");

}


?>
