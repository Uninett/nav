<?php


function s_header($title=""){
  $this_title = "NAV";
  if ($title){
    $title = "$this_title :: $title";
  }
  
  return "\n<!DOCTYPE html\n\tPUBLIC \"-//W3C//DTD XHTML 1.1//EN\"\n\t\"http://nidarholm.com/webdocs/system/format/xhtml1-transitional.dtd\"><html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"no\">\n\n<head>\n<meta http-equiv=\"Pragma\" content=\"no-cache\"/>\n\t<meta http-equiv=\"Cache-Control\" content=\"no-cache\"/>\n\t<meta http-equiv=\"Content-Language\" content=\"no-bm\"/>\n\t<meta http-equiv=\"Content-Type\" content=\"text/html;charset=iso-8859-1\"/>\n\t<title>$title</title>\n<link rel=\"stylesheet\" type=\"text/css\" href=\"style.css\"/>\n</head>\n\n<body>\n";

}

function s_footer(){
  return "\n\t</body>\n</html>";
}




?>