<?php Header ("Content-type: image/png"); 
$font = "kulfont.ttf";
$tsize = imagettfbbox(32,0,$font,$overskrift);
$dx = abs($tsize[2]-$tsize[0]);
$dy = abs($tsize[5]-$tsize[3]);
$im = imagecreate ($dx+80,48); 
$black = ImageColorAllocate ($im, 0, 0, 0); 
$color_nav = ImageColorAllocate ($im, 71, 100, 144); 
$color_white = ImageColorAllocate ($im, 255, 255, 255);
imagefill($im,0,0,$color_nav);
ImageTTFText ($im, 32, 0, 0,35, $color_white,$font,$overskrift); 
ImageTTFText ($im, 12, 0, $dx+40,$dy+5, $color_white,$font,NAV); 
Imagepng($im); ImageDestroy ($im); ?>
