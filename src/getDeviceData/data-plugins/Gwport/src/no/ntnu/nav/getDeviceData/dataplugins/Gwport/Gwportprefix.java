package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.util.*;

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

	void setHsrp(boolean h) { hsrp = h; }
	void setPrefix(Prefix p) { prefix = p; }

	public boolean equalsGwportprefix(Gwportprefix gp) {
		return (gp != null &&
						hsrp == gp.hsrp);
	}

	public boolean equals(Object o) {
		return (o instanceof Gwportprefix && 
						equalsGwportprefix((Gwportprefix)o));
	}

	public String toString() {
		return "gwip="+gwip + " hsrp="+hsrp + " prefix="+prefix + " ("+Integer.toHexString(hashCode())+")";
	}

}
