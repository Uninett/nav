<?php Header ("Content-type: image/png"); 
$font = "kulfont.ttf";
$tsize = imagettfbbox(12,0,$font,$tekst);
$dx = abs($tsize[2]-$tsize[0]);
$dy = abs($tsize[5]-$tsize[3]);
$im = imagecreate ($dx+3,$dy+4); 
$black = ImageColorAllocate ($im, 0, 0, 0); 
$color_nav = ImageColorAllocate ($im, 71, 100, 144); 
$color_white = ImageColorAllocate ($im, 255, 255, 255);
$tekst = ucfirst($tekst);
imagefill($im,0,0,$color_nav);
ImageTTFText ($im, 12, 0, 0,12, $color_white,$font,$tekst); 
//ImageTTFText ($im, 12, 0, $dx+40,$dy+5, $color_white,$font,NAV); 
Imagepng($im); ImageDestroy ($im); ?>
