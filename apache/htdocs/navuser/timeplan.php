<?php

function makeBox($img, $shaddow, $up, $down, $color, $text) {
  $bg = ImageColorAllocate($img, 150, 150, 150);
  $black = ImageColorAllocate($img, 0,0,0);
  
  ImageFilledRectangle($img, 50+$shaddow, $up+$shaddow, 
		       180+$shaddow, $down+$shaddow, $black);
# Lager boks med ramme
  ImageFilledRectangle($img, 50, $up, 180, $down, $color);
  ImageRectangle($img, 50, $up, 180, $down, $black);
  
# Legger inn tekst
  if ( ($down-$up) > 12) {
    ImageString($img, 3, 55, $up + 3 , $text, $black);
  }
}

function makeZone($img, $h, $m, $h2, $m2, $col, $forcewrap) {
  
  $start = (60*24 + $h * 60 + $m - 60 * 6) % (60*24);
  $stop = (60*24 + $h2 * 60 + $m2 - 60 * 6) % (60*24);

  $klokke = substr("0" . $h, strlen("0" . $h) - 2 ) . ":";
  $klokke .= substr("0" . $m, strlen("0" . $m) - 2 ) . " - ";
  $klokke .= substr("0" . $h2, strlen("0" . $h2) - 2 ) . ":";
  $klokke .= substr("0" . $m2, strlen("0" . $m2) - 2 );
  
  $bg = ImageColorAllocate($img, 150, 150, 150);
  $black = ImageColorAllocate($img, 0,0,0);
  $arrow = ImageColorAllocate($img, 150,150,150);

  if ($start < $stop) {
    $up = 10 + round( (360*$start) / (24*60)) ;
    $down = 6 + round( (360*$stop) / (24*60));

    if ( ($down-$up) > 2) {
      makeBox($img, 2, $up, $down, $col, $klokke);
    }

  } else if (($start > $stop) OR ($forcewrap)) {

    $up = 10 + round( (360*$start) / (24*60)) ;
    $down = 6 + 360;
    if ( ($down-$up) > 2) {
      makeBox($img, 2, $up, $down, $col, $klokke);
    }

    $up = 10;
    $down = 6 + round( (360*$stop) / (24*60));
    if ( ($down-$up) > 2) {
      makeBox($img, 2, $up, $down, $col, $klokke);
    }

  }

}

if ($debug != 1) { Header("Content-type: image/png"); }
$string=implode($argv," ");

$im = ImageCreate(200,380);

$white = ImageColorAllocate($im, 255, 255, 255);
ImageColorTransparent($im, $white);


$or2 = ImageColorAllocate($im, 180, 180, 30);
$black = ImageColorAllocate($im, 0,0,0);

$px = (imagesx($im)-7.5*strlen($string))/2;


for ($i = 0; $i < 24; $i++ ) {
  $klokke = (6 + $i) % 24;
  ImageString($im,1, 15,10 + $i*15, substr("0" . $klokke, 
					   strlen("0" . $klokke) -2 ),
	      $black);
  ImageLine($im, 30, 10 + 15*$i, 40, 10 + 15*$i, $black);
  ImageLine($im, 35, 17 + 15*$i, 40, 17 + 15*$i, $black);

  $bgcol[0] = ImageColorAllocate($im,  51, 51, 255);
  $bgcol[1] = ImageColorAllocate($im, 102, 102, 255);

  if ($i % 2 == 0) {
    ImageFilledRectangle($im, 40, 10 + 15*$i, 190, 40 + 15*$i, 
			 $bgcol[(($i % 4) / 2) ] );
  } 

}

#    ImageString($im,1, 150,10 + $i*15, "yo." . (($i % 4) / 2), $black);

ImageRectangle($im, 40, 10, 190, 370, $black);

$col[0] = ImageColorAllocate($im, 255, 153,  51);
$col[1] = ImageColorAllocate($im, 204, 153, 204);
$col[2] = ImageColorAllocate($im,   0, 153, 204);
$col[3] = ImageColorAllocate($im, 204, 153, 102);
$col[4] = ImageColorAllocate($im, 153, 153, 102);
$col[5] = ImageColorAllocate($im, 153, 204,  51);
$col[6] = ImageColorAllocate($im,   0, 102, 102);
$col[7] = ImageColorAllocate($im, 255, 255, 102);


// hvis bare et force wraparaound
if (sizeof($t) == 1) {
  makeZone($im, $t[0], $m[0], $t[0], $m[0], $col[0], true); 

} else {

// $t time   $m minutt  $col farger $t teller
  for ($i = 0; $i < sizeof($t) ; $i++) {

    makeZone($im, $t[$i], $m[$i], 
	     $t[($i + 1) % sizeof($t)], 
	     $m[($i + 1) % sizeof($t)], 
	     $col[$i % sizeof($col)],
	     false);
  }
}

if ($debug != 1) { ImagePng($im); }
ImageDestroy($im);

?>
