<?php

include('formatting.inc.php');
include('access.inc.php');
include('file.inc.php');

list($lock,$user) = locked($file);

if(isset($file) && $lock == 1 && $user == user_res()){
  
  unlock_nrs($file);
  if(!$commit){
      copy(path_nrt($file),path_file($file));
  }

  unlink(path_nrt($file));
  exec("/usr/bin/ci -u -m'".user_res().":\t$commit' ".path_file($file));

}

header("Location: index.php");

?>
