<?php
/*
 * listing.php
 * (c) Andreas Åkre Solberg (andrs@uninett.no) - Mai, 2002
 *
 * Dette er et generelt bibliotek for å holde styr på tabeller og skrive de ut i sortert rekkefølge
 *
 *

 */


/*
 * Dette er en klasse om kan puttes inn som et element i et listing objekt. Den kan inneholde html, og puttes inn i en
 * celle med full colspan i tabellen som listes ut med lister->getHTML
 */
class HTMLCell {
  var $tekst;

  function HTMLCell($tekst) {
    $this->tekst = $tekst;
  }
  
  function getHTML() {
    return $this->tekst;
  }
}


/*
 * Lister er klassen som holder hele tabellen og den har funksjoner for √Ç legge til hente ut og sortere
 * rader
 *
 */
class Lister {

	var $lid; // The listings identification (used to fetch sort parameters from sessioncoockies)
	var $list; // the list
	var $param; // liste over parametere som skal være med i url'en i søkefeltene.
	var $labels; // the labels of the list (to be in the header of the table)
	var $sorts;	// Bolsk om en kolonne skal kunne sorteres
	var $asort;	// Hvilke kolonne skal være sortert for øyeblikket.
	var $cols; // Column width array.
	var $aligns; // alignments on columns
	var $action; // submenu..
	var $highlight; // which row to highlight?

	// This constructor initializes the table.
	function Lister($id, $labels, $c, $align, $isorts, $defaultsort) {

		// ID på tabellen
		$this->lid = $id;
		  
		// Overskrift på kolonnene
		$this->labels = $labels;

		// column sizes in percent.
		$this->cols = $c;

		// ALignment for cellene
		$this->aligns = $align;
		
		// bool skal kolonnen kunne sorteres
		$this->sorts = $isorts;
		
		if (!session_get('listing_sort-' . $this->lid)) {
			session_set('listing_sort-' . $this->lid, $defaultsort );
		}
  	}
  
  	function highlight($row) {
  		if (isset($row)) {
  			$this->highlight = $row;
  		} else {
  			$this->highlight = undef;
  		}
  		
  	}
  
 	// Sett og hent sorteringskriterie
 	function setSort($setsort, $id) {
 		if ($this->lid == $id) {
			session_set('listing_sort-' . $this->lid,  $setsort);
		}
 	}

	function getSort() {
		return session_get('listing_sort-' . $this->lid);
	}

	// Simply add a row
	function addElement($newElement) {
		$this->list[] = $newElement;
	}

	// Get an element from the table
	function getElement($nr) {
		return $this->list[$nr];
	}

	// This function lists the elements in a html table - very beautiful.
	function getHTML() {

		// Sort the table
		$s = "<table class=\"listingTable\" width=\"100%\" border=0 cellpadding=0 cellspacing=0>\n";

		// Go for the table labels
		$s .= "<tr>";
		$col = 0;

		foreach ($this->labels as $key => $label) {

			$s .= "<td class=\"listingLabel\" align=\"" . $this->aligns[$col] . "\">";

			if ($this->sorts[$col] ) {	    	
				$s .= "<a class=\"sort\" href=\"index.php?sortid=" . $this->lid ."&sort=$key\">";
			}	
			$s .= $label;
			
			if ($this->sorts[$col] ) {
				$s .= "</a>";
			}

			if ( $this->sorts[$col] ) {
				if (session_get('listing_sort-' . $this->lid) == $col) {
					$s .= "<img src=\"icons/sort1.png\" alt=\"sortering\">";
				} else {
					$s .= "<img src=\"icons/sort0.png\" alt=\"sortering\">";		
				}
			}
			
		$s .= "</td>\n";
		$col++;
    }

    $s .= "</tr>\n";

    // Switching colors for each row:
    $row[0] = 'listingRowA'; $row[1] = 'listingRowB';
    $nr = -1;

    if (isset($this->list) ) {
    	// Go for the table elements
    	foreach ($this->list as $element) {
    		if (!get_Class($element)) $nr++;
			if (isset($this->highlight) AND $nr == $this->highlight) $cclass = 'listingHL'; else $cclass = $row[($nr % 2)];  
			  	
			if (get_Class($element)) {
				$s .= "<tr class=\"". $cclass . "\"><td colspan=\"" . sizeof($this->labels) . "\">" .
	    		$element->getHTML() . "</td></tr>\n";
			} else {
	  			$s .= "<tr class=\"". $cclass . "\">\n";
				$col = 0; 
	  			foreach ($element as $key => $field) {
	    			$s .= " <td class=\"listingField\" width=\"" . $this->cols[$col] .  
					      "%\" align=\"" . $this->aligns[$col] . "\">$field</td>\n";
	  				$col++;
	  			}
				$s .= "</tr>\n";
			}
      	}
    } else {
    	$s .= "<tr><td colspan=\"". sizeof($this->labels) . "\">" . gettext("Ingen elementer funnet") . ".</td></tr>\n";
    }
    $s .= "</table>";

    return $s;
  }
  

}

?>
