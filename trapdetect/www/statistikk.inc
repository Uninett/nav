<?php

function tegnBilde($data, $max) {

  $antall = sizeof ($data);
	
# Størrelse på bildet
  $xsize = 700;
  $ysize = 50*$antall;
	
  $image = imagecreate($xsize, $ysize);
	
# Mekker farger
  $lightgrey = imagecolorallocate ($image, 182, 182, 182);
  $blue = imagecolorallocate ($image, 51, 153, 255);
  $black = imagecolorallocate ($image, 0, 0, 0);
  $grey = imagecolorallocate ($image, 120, 120, 120);
  $darkgrey = imagecolorallocate ($image, 70, 70, 70);
	
# Fyller bakgrunnsfarge
  imagefill ($image, 0, 0, $lightblue);

  $teller = 0;
# Beregner antall skillelinjer
  $antall_linjer = $max;
  $scale = 1;

  while ($antall_linjer > 20) {
    $antall_linjer = $antall_linjer/2;
    $scale = $scale * 2;
  }
	
# Tegner opp vertikale skillelinjer
  $diff = $xsize/$antall_linjer;
  $tall = 0;
  while (($x*0.9) < $xsize) {
    $x += $diff;
    imageline ($image, $x*0.9, 0, $x*0.9, $ysize, $grey);
    $tall = $tall + $scale;
    imagestring ($image, 5, ($x-7)*0.9, 0, $tall, $black);
  }
  for ($i=5;$i<$antall_linjer;$i+=5) {
    $x = $i*$diff;
    imageline ($image, $x*0.9, 0, $x*0.9, $ysize, $darkgrey);
  }
	
# Tegner opp firkant rundt hele
  imagerectangle ($image, 0, 0, $xsize-1, $ysize-1, $black);
	
# Saver en imagemap
  array ($imagemap);

  if ($antall > 0) {
    $teller = 0;
    $bredde = ($ysize-10)/$antall;
    $y = $bredde/6+10;
	
# Tegner søyler
    for ($i = 0; $i < $antall; $i++) {
      $navn = key ($data);
      $xx = ($data[$navn]/$scale)*$diff*0.9;
      if ($xx < 2) {
	$xx = 2;
      }
      $yy = $y + (($bredde*2)/3);
# xx=nh, x=øv, y=øv, yy=nh
      imagefilledrectangle ($image, 1, $y, $xx, $yy, $blue);
      $imagemap[$navn] = array(1, $y, $xx, $yy);
      imagestring ($image, 5, 10, $y + 3, $navn, $black);
      imagestring ($image, 5, 10, $y + 16, $data[$navn], $black);
      next ($data);
      $y += $bredde;
      $teller++;
    } 
  } else {
    imagestring ($image, 5, 10, 10, "Ingen data tilgjengelig", $black);
  }

# Saver bilde
  $bildenavn = date("dHis");
  imagepng ($image,"pics/$bildenavn.png");
  return array ($imagemap, $bildenavn);

}

function lagData($type, $filename) {

  $innhold = file($filename);

  array ($data);
  $max = 0;
  $teller = 0;

  if ($type == "oid") {
    while ($innhold[$teller]) {
      list ($name,$oid,$verdi) = split(" ", $innhold[$teller]);
      settype ($verdi, "integer");

      $data[$oid] += $verdi;
      if ($data[$oid] > $max) {
	$max = $data[$oid];
      }
      $teller++;
    }		
  } else {
    while ($innhold[$teller]) {
      list ($name,$oid,$verdi) = split(" ", $innhold[$teller]);
      settype ($verdi, "integer");

      $data[$name] += $verdi;
      if ($data[$name] > $max) {
	$max = $data[$name];
      }
      $teller++;
    }
  }

  return array ($data, $max);

}

function lagDataDet($type, $filename, $streng) {

  $innhold = file($filename);

  array ($data);
  $max = 0;
  $teller = 0;

  if ($type == "oid") {
    while ($innhold[$teller]) {
      if (preg_match("/$streng/", $innhold[$teller])) {
	list ($name,$oid,$verdi) = split(" ", $innhold[$teller]);
	settype ($verdi, "integer");

	$data[$oid] += $verdi;
	if ($data[$oid] > $max) {
	  $max = $data[$oid];
	}
      }
      $teller++;
    }
  } else {
    while ($innhold[$teller]) {
      if (preg_match("/$streng/", $innhold[$teller])) {
	list ($name,$oid,$verdi) = split(" ", $innhold[$teller]);
	settype ($verdi, "integer");

	$data[$name] += $verdi;
	if ($data[$name] > $max) {
	  $max = $data[$name];
	}
      }
      $teller++;
    }
  }

  return array ($data, $max);

}

?>