<?php Header ("Content-type: image/png"); 
$im = imagecreate (1,1); 
$color_nav = ImageColorAllocate ($im, 71, 100, 144); 
imagefill($im,0,0,$color_nav);
Imagepng($im); ImageDestroy ($im); ?>
