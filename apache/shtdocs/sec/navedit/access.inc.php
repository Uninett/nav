<?php
clearstatcache();
function user_res(){
  $user = $_SERVER["PHP_AUTH_USER"];
  return $user;
}
function user_web(){
  list($no,$user_web) = split("=",file_get_contents("../../../../etc/conf/navedit/navedit.conf"));
  return trim($user_web);
}
function separator($string_with_separators){
  $separators = array(":","=",",",";");
  $max = 0;
  $max_separator = "";
  foreach($separators as $s){
    $sep = substr_count($string_with_separators,$s);
    if($sep > $max){
      $max = $sep;
      $max_separator = $s;
    }
  }
  return $max_separator;
}
function diemessage($message){
  die($message);
}
function path_navadmin(){
  return "/usr/local/nav/navme/apache/shtdocs/sec/navedit/";
}
function file_list(){
  $file_list = file("/usr/local/nav/local/etc/conf/navedit/files.conf");
  $file_list = array_map("trim",$file_list);
  return $file_list;
}
$filliste = file_list();/*array("/home/gartmann/htdocs/navadmin/filer/fal.txt","/home/gartmann/htdocs/navadmin/filer/fil.txt","/home/gartmann/htdocs/navadmin/filer/ful.txt","/home/gartmann/htdocs/navadmin/filer/fyl.txt");*/


function path_file($file){
  global $filliste;
  if(is_file($f = $filliste[$file])){
    return $f;
  }
}

function list_files(){
  global $filliste;
  return $filliste;
}

function path_nrt($file){
  return path_navadmin()."/filer/NRT/".$file.",t";
}

function path_nrs($file){
  return path_navadmin()."/filer/NRS/".$file.",n";
}

function lock_nrs($file){

  return file_set_contents(path_nrs($file),user_res());
}

function unlock_nrs($file){
  //d*iter i hva det står i låsefila, bare låser opp
  return unlink(path_nrs($file));
}

function locked_nrs($file){
  /* returnerer hvem som har låst fila via web */
  $file_nrs = path_nrs($file);
  if(is_file($file_nrs)){
    $owner = trim(file_get_contents($file_nrs));
  }
  return $owner;
}

function locked_rcs($file){
  $filename = path_file($file);
  /* returnerer hvem som har låst fila via shell */
  if(owner_write_right($filename)){
    $owner = posix_getpwuid(fileowner($filename));
  }
  return $owner['name'];
}

function file_rcs($file){
  $pathinfo = pathinfo(path_file($file));
  $file_rcs = $pathinfo['dirname']."/RCS/".$pathinfo['basename'].",v";
  if(is_file($file_rcs)){
    return 1;
  }
}

function file_nrs($file){
  return 1;
}

function owner($file){
  list($type,$owner) = locked($file);
  if($type == 1 && $owner == user_res()){
    return 1;
  }
}

function locked($file){
  $file_nrs = file_nrs($file);

  //fila må finnes i liste over gyldige filer, hvis ikke: stor sikkerhetsrisk
  if(!$file_nrs){

    return array(4,"nofile");
  } else {

    $file_rcs = file_rcs($file);

    if(!$file_rcs){

      return array(3,"nofile");
    } else {

      $owner_rcs = locked_rcs($file);

      if($owner_rcs && $owner_rcs != user_web()){

	//print "fila er låst via shell-RCS av $owner_rcs. For å få tilgang til fila, må den låses opp med \'ci\'-kommandoen av eieren av fila";
	return array(2,$owner_rcs);

      } else {

	$owner_nrs = locked_nrs($file);

	if($owner_nrs){

	  return array(1,$owner_nrs);
	  //print "fila er låst via web (disse sidene) av $owner_nrs";
	}

      }
    }
  }
}

function owner_write_right($file){
  if(is_file($file)){
    $perms = fileperms($file);
    if($perms & 00200){
      return 1;
    }
  }
}
function file_get_contents($filename, $use_include_path = 0) {
  $fd = fopen ($filename, "r", $use_include_path);
  $contents = fread($fd, filesize($filename));
  fclose($fd);
  return $contents;
}

function file_set_contents($filename, $contents = "", $use_include_path = 0) {
  if(!$contents) die ("You have to put something into the file");
  $fd = fopen ($filename, "w", $use_include_path);
  $contents = fwrite($fd, $contents);
  fclose($fd);
  return 1;
}


function new_locked_rcs($file){
  if($lock_info = shell_exec("rlog -h -L ".path_file($file))){
    $lock_info = split("\n",$lock_info);
    $lock_array = split(":",$lock_info[6]);
    return trim($lock_array[0]);
  }
}

function file_is_not_new($file){
  if(time() - filemtime(path_file($file)) > 36){
    return 1;
  }
}

function errormessage($error=0){

  if($error == "nofile"){

    $message = "The file you requested does not exist";
    
  } elseif($error == "notmyfile"){

    $message = "You do not have the right privilegies to do as you want";

  }

  if($error){
  return "<div id=\"error\"><img src=\"ikoner/error.png\" alt=\"error\"/><br/>".$message."</div>";;
  }
}
function get_fileinfo($f,$filliste=""){

  if(!$filliste){
    $filliste = list_files();
  }
  $name = basename($filliste[$f]);
  $get = locked($f);
  
  if(is_file(path_file($f))){
    $timestamp = filectime(path_file($f));
    if($timestamp - time() > 43200){
      $timestamp = "(<i>".date("j.n.Y H:i",$timestamp)."</i>)";
    } else {
      $timestamp = "(<i>".date("H:i",$timestamp)."</i>)";
    }
  }
  if($get[0] == 1){
    if($get[1] != user_res() && file_is_not_new($f)){
      $steal = ", but that was a long time ago, you may <a href=\"steal.php?file=$f\">steal</a> it now";
    }
    $lock = "<img src=\"ikoner/encrypted.png\" alt=\"NAVlocked\"/> Låst via NAV av <b>".$get[1]."</b> ".$timestamp.$steal;
  } elseif($get[0] == 2){
    $lock = "<img src=\"ikoner/encrypted.png\" alt=\"RCSlocked\"/> Låst via RCS i shell av <b>".$get[1]."</b> ".$timestamp;
  } elseif($get[0] == 3){
    $lock = "<img src=\"ikoner/cancel.png\" alt=\"NOfile\"/> Fila ligger ikke lagret i RCS, du kan ikke redigere denne.";
  } else {
    $lock = "<img src=\"ikoner/mime.png\" alt=\"UNlocked\"/> Fila er <b>ikke</b> låst";
  }
  return "<div class=\"menuitem\"><h2><a href=\"lock.php?file=$f\">$name</a></h2><p>$lock</p><p>$filliste[$f]</p></div>";

}

?>