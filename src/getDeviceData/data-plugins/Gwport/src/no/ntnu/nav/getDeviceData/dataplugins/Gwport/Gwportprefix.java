package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.*;

import no.ntnu.nav.logger.*;

/**
 * Contain Gwportprefix data
 */

class Gwportprefix
{
	private String gwip;
	private boolean hsrp;
	private Prefix prefix;

	Gwportprefix(String gwip, boolean hsrp, Prefix prefix) {
		this.gwip = gwip;
		this.hsrp = hsrp;
		this.prefix = prefix;
	}

	String getGwip() { return gwip; }
	boolean getHsrp() { return hsrp; }
	Prefix getPrefix() { return prefix; }


}
