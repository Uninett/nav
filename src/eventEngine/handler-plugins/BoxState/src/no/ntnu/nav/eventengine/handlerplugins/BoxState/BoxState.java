package no.ntnu.nav.eventengine.handlerplugins.BoxState;

import no.ntnu.nav.eventengine.*;
import java.util.*;


public class BoxState implements EventHandler
{

	public String[] handleEventTypes()
	{
		return new String[] { "boxState" };
	}

	public void handle(Event e)
	{
		outld("BoxState handeling event: " + e);


	}


	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }

}
