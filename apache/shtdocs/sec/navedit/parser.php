<?php
include('access.inc.php');
include('file.inc.php');

function strip_fnutts($text){
  $text = str_replace("\\\"","\"",$text);
  return $text;
}

if(isset($file) && $operation == "update" && isset($row) && $felt){

  if(is_array($felt)){
    // rad med data
    $contents = strip_fnutts(join(":",$felt))."\n";
  } else {
    //kommentar
    $contents = "# ".strip_fnutts($felt)."\n";
  }

  $file_array = file(path_file($file));
  $file_array[$row] = $contents;

  $handle = fopen(path_file($file), 'w');
  fwrite($handle, join("",$file_array));
  fclose($handle);


} elseif (isset($file) && $operation == "insert" && isset($row) && $felt){

  if(is_array($felt)){
    // rad med data
    $contents = strip_fnutts(join(":",$felt))."\n";
  } else {
    //kommentar
    $contents = "# ".strip_fnutts($felt)."\n";
  }

  $file_array = file(path_file($file));
    
  $new_file_array = array();

  for($i = 0; $i<$row; $i++){
    $new_file_array[$i] = $file_array[$i];
  }

  $new_file_array[$row] = $contents;
    
  for($i = $row; $i < sizeof($file_array) + 1; $i++){
    $new_index = $i + 1;
    $new_file_array[$new_index] = $file_array[$i];
  }

  $handle = fopen(path_file($file), 'w');
  fwrite($handle, join("",$new_file_array));
  fclose($handle);

} elseif (isset($file) && $operation == "delete" && isset($row)){

  $file_array = file(path_file($file));
    
  $new_file_array = array();

  for($i = 0; $i<$row; $i++){
    $new_file_array[$i] = $file_array[$i];
  }

  /* Her blir aktuell rad ikke tatt med i den nye versjonen av fila */
    
  for($i = $row; $i < sizeof($file_array) - 1; $i++){
    $new_file_array[$i] = $file_array[$i+1];
  }

  $handle = fopen(path_file($file), 'w');
  fwrite($handle, join("",$new_file_array));
  fclose($handle);

} elseif (isset($file) && $operation == "advanced" && $contents){

  $contents = strip_fnutts($contents);
  
  $fh = fopen(path_file($file),"w");
  fwrite($fh,$contents);
  fclose($fh);
  
} else {

  print $QUERY_STRING;
  print "ugyldig";

}

header("Location:view.php?file=$file");
?>