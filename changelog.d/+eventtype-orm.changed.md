The snmptrapd linkupdown and ups handlers now ensure their event and alert
types exist via Django's ORM instead of talking to the database directly.
